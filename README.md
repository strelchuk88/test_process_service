# Payment Processing Service

Асинхронный сервис процессинга платежей: принимает платёж по API, обрабатывает его через эмулятор платёжного шлюза и уведомляет клиента webhook'ом.

**Стек:** FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), PostgreSQL, RabbitMQ (FastStream), Alembic, Docker Compose.

## Запуск

```bash
cp .env.example .env
make all
```

`make all` поднимает:

| Сервис | Адрес | Что делает |
|---|---|---|
| `web` | http://localhost:8000/api/docs | API и outbox relay; при старте применяет миграции |
| `consumer` | — | воркер (`worker.py`): обрабатывает платежи из очереди |
| `postgres` | localhost:5432 | БД |
| `rabbitmq` | http://localhost:15672 (guest/guest) | брокер и UI |
| `webhook-mock` | http://localhost:9000/received | тестовый приёмник webhook'ов |

Порты и пароли задаются в `.env`. Отдельные части: `make storages`, `make rabbit`, `make app`.

## API

Все запросы требуют заголовок `X-API-Key` (значение `API_KEY` из `.env`).

### Создание платежа

`POST /api/v1/payments`, обязательный заголовок `Idempotency-Key`.

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "X-API-Key: super-secret-api-key" \
  -H "Idempotency-Key: order-42" \
  -H "Content-Type: application/json" \
  -d '{
        "amount": "1500.50",
        "currency": "RUB",
        "description": "Order #42",
        "metadata": {"order_id": 42},
        "webhook_url": "http://webhook-mock:9000/webhook"
      }'
```

```json
HTTP/1.1 202 Accepted
{"payment_id": "bd9d5834-...", "status": "pending", "created_at": "2026-10-08T14:26:01.854288Z"}
```

| Ответ | Когда |
|---|---|
| `202` | платёж принят; повтор с тем же ключом и телом возвращает тот же платёж |
| `409` | `Idempotency-Key` уже использован с другим телом |
| `401` | нет или неверный `X-API-Key` |
| `422` | ошибка валидации: сумма ≤ 0, неизвестная валюта, нет `Idempotency-Key` и т. п. |

### Получение платежа

```bash
curl http://localhost:8000/api/v1/payments/<payment_id> -H "X-API-Key: super-secret-api-key"
```

```json
{
  "payment_id": "bd9d5834-...",
  "amount": "1500.50",
  "currency": "RUB",
  "description": "Order #42",
  "metadata": {"order_id": 42},
  "status": "succeeded",
  "idempotency_key": "order-42",
  "webhook_url": "http://webhook-mock:9000/webhook",
  "created_at": "2026-10-08T14:26:01.854288Z",
  "processed_at": "2026-10-08T14:26:06.483403Z"
}
```

### Webhook

После обработки consumer отправляет `POST` на `webhook_url`:

```json
{
  "event": "payment.succeeded",
  "payment_id": "bd9d5834-...",
  "status": "succeeded",
  "amount": "1500.50",
  "currency": "RUB",
  "description": "Order #42",
  "metadata": {"order_id": 42},
  "created_at": "...",
  "processed_at": "..."
}
```

`event` — `payment.succeeded` или `payment.failed`. Доставка at-least-once: получатель должен быть готов к повторам и различать их по `payment_id`.

Для проверки ретраев и DLQ укажите `"webhook_url": "http://webhook-mock:9000/fail"` — этот адрес всегда отвечает 500.

## Как это работает

```
POST /payments ──► [payments + outbox] ──► outbox relay ──► payments (topic) ──► payment.create ──► consumer
                    одна транзакция                                                  │   ▲
                                                                                     │   │ TTL истёк
                                                  ошибка, попытка N < max ───────────┼─► payment.create.retry.N
                                                                                     │
                                                  попытка = max: reject ─────────────┴─► payments.dlx (fanout) ──► payment.dlq
```

### Outbox pattern

Платёж и событие `payment.created` записываются в таблицы `payments` и `outbox` в одной транзакции, поэтому события не теряются, даже если RabbitMQ недоступен в момент запроса. Outbox relay — фоновая задача в `web` — раз в секунду забирает неопубликованные события (`FOR UPDATE SKIP LOCKED`), публикует их и ставит `published_at` только после подтверждения брокера. Ошибки публикации записываются в `attempts` и `last_error`, событие повторяется в следующей итерации.

### Consumer

1. Получает сообщение из `payment.create`.
2. Эмулирует шлюз: 2–5 секунд, 90% успех, 10% отказ. Отказ шлюза — это результат платежа (`failed`), а не ошибка обработки.
3. Обновляет статус в БД.
4. Отправляет webhook.

Обработка идемпотентна: платёж списывается только в статусе `pending`, статус меняется условным `UPDATE ... WHERE status = 'pending'`. Повторная доставка того же сообщения, например после упавшего webhook'а, не списывает платёж второй раз, а только повторяет webhook.

### Retry и DLQ

Любая ошибка обработки (недоступен webhook, БД и т. п.) повторяется с экспоненциальной задержкой. Сообщение отправляется в очередь задержки своей попытки, по истечении TTL RabbitMQ возвращает его в `payment.create`:

| Попытка | Ошибка → куда | Задержка |
|---|---|---|
| 1 | `payment.create.retry.1` | 2 с |
| 2 | `payment.create.retry.2` | 4 с |
| 3 | reject → `payments.dlx` → `payment.dlq` | — |

Номер попытки передаётся в заголовке `x-attempt`. Для каждой попытки своя очередь с фиксированным TTL: при TTL на отдельных сообщениях длинная задержка в начале очереди задерживала бы и короткие. Сообщения с невалидным телом и платежи, которых нет в БД, уходят в DLQ сразу — повтор им не поможет.

Число попыток и базовая задержка настраиваются через `RABBIT__MAX_ATTEMPTS` и `RABBIT__RETRY_BASE_DELAY`.

## Структура

```
app/
├── main.py                         # точка входа API: FastAPI, роутеры, обработчики ошибок
├── worker.py                       # точка входа воркера: FastStream, объявление топологии при старте, сборка зависимостей
│
├── api/                            # HTTP
│   ├── dependencies.py             # сессия БД, use case'ы, проверка X-API-Key
│   ├── exception_handlers.py       # AppError → HTTP-ответ
│   └── v1/
│       ├── payments.py             # POST /api/v1/payments, GET /api/v1/payments/{id}
│       └── schemas.py              # схемы запросов и ответов
│
├── consumers/                      # обработчики сообщений RabbitMQ
│   └── payment.py                  # payment.create → обработка, ретрай или DLQ
│
├── application/                    # прикладная логика
│   ├── use_cases/
│   │   ├── create_payment.py       # платёж + outbox-событие в одной транзакции, идемпотентность
│   │   └── process_payment.py      # шлюз → статус → webhook
│   └── services/
│       ├── payment.py              # получение платежа
│       ├── gateway.py              # эмулятор платёжного шлюза
│       └── webhook.py              # отправка webhook'а
│
├── domain/
│   ├── enums/payment.py            # CurrencyEnum, PaymentStatus
│   └── exceptions.py               # ошибки приложения (AppError и наследники)
│
├── infrastructure/
│   ├── broker/
│   │   ├── broker.py               # подключение к RabbitMQ
│   │   ├── config.py               # имена exchange'ей и очередей
│   │   ├── topology.py             # объявление exchange'ей, очередей, retry и DLQ
│   │   ├── messages.py             # схема сообщения, заголовок попытки
│   │   └── retry.py                # отправка в retry-очередь
│   ├── database/
│   │   ├── models/                 # PaymentModel, OutboxModel
│   │   └── repositories/           # PaymentRepository, OutboxRepository
│   └── outbox/
│       └── relay.py                # публикация событий из outbox в RabbitMQ
│
├── core/
│   ├── settings.py                 # настройки из .env
│   ├── database.py                 # движок и фабрика сессий
│   └── lifespan.py                 # старт API: БД, брокер, топология, outbox relay
│
├── alembic/                        # миграции
└── tools/
    └── webhook_mock.py             # тестовый приёмник webhook'ов
```

## Ограничения

- RabbitMQ не позволяет менять тип и аргументы существующих очередей и exchange'ей. После изменения топологии старые объекты нужно удалить: в UI или через `rabbitmqctl delete_queue`.
- Webhook доставляется at-least-once: если сбой случится между успешной отправкой и подтверждением сообщения, получатель получит webhook повторно.

DC = docker compose
EXEC = docker exec -it
LOGS = docker logs
ENV_FILE = .env
APP_FILE = docker_compose/app.yaml
STORAGES_FILE = docker_compose/storages.yaml

.PHONY: app
app:
	${DC} --env-file ${ENV_FILE} -f ${APP_FILE} up --build -d

.PHONY: storages
storages:
	${DC} --env-file ${ENV_FILE} -f ${STORAGES_FILE} up --build -d

.PHONY: all
all:
	${DC} --env-file ${ENV_FILE} -f ${STORAGES_FILE} -f ${APP_FILE} up --build -d

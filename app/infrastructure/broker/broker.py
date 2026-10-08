from faststream.rabbit import RabbitBroker

from core.settings import RabbitSettings


class Broker:
    def __init__(self, settings: RabbitSettings) -> None:
        self.rabbit = RabbitBroker(str(settings.url))

    async def start(self) -> None:
        await self.rabbit.start()

    async def stop(self) -> None:
        await self.rabbit.stop()

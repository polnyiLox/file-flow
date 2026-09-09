class AnalyticsService:
    def __init__(self, repository) -> None:
        self._repository = repository

    async def overview(self) -> dict:
        return await self._repository.overview()

    async def uploads(self, page: int, page_size: int) -> list[dict]:
        return await self._repository.get_events(
            ["file.uploaded"], (page - 1) * page_size, page_size,
        )

    async def processing(self, page: int, page_size: int) -> list[dict]:
        return await self._repository.get_events(
            ["file.processing_started", "file.processed", "file.processing_failed"],
            (page - 1) * page_size, page_size,
        )

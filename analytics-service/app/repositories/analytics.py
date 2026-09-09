from pymongo.errors import DuplicateKeyError


class AnalyticsRepository:
    def __init__(self, database) -> None:
        self._collection = database["analytics_events"]

    async def create_indexes(self) -> None:
        await self._collection.create_index("event_id", unique=True)
        await self._collection.create_index([("event_type", 1), ("occurred_at", -1)])

    async def save_event(self, event) -> bool:
        document = event.model_dump(mode="json", exclude_none=True)
        document["occurred_at"] = event.occurred_at
        try:
            await self._collection.insert_one(document)
        except DuplicateKeyError:
            return False
        return True

    async def overview(self) -> dict:
        cursor = await self._collection.aggregate([
            {"$group": {
                "_id": None,
                "files_uploaded": {"$sum": {"$cond": [{"$eq": ["$event_type", "file.uploaded"]}, 1, 0]}},
                "files_processed": {"$sum": {"$cond": [{"$eq": ["$event_type", "file.processed"]}, 1, 0]}},
                "files_failed": {"$sum": {"$cond": [{"$eq": ["$event_type", "file.processing_failed"]}, 1, 0]}},
                "average_processing_ms": {"$avg": {"$cond": [
                    {"$eq": ["$event_type", "file.processed"]}, "$payload.processing_time_ms", None,
                ]}},
            }},
            {"$project": {"_id": 0}},
        ])
        rows = await cursor.to_list(length=1)
        if not rows:
            return {"files_uploaded": 0, "files_processed": 0, "files_failed": 0, "average_processing_ms": 0}
        result = rows[0]
        result["average_processing_ms"] = round(result["average_processing_ms"] or 0, 2)
        return result

    async def get_events(self, event_types: list[str], offset: int, limit: int) -> list[dict]:
        cursor = self._collection.find(
            {"event_type": {"$in": event_types}}, {"_id": 0},
        ).sort([("occurred_at", -1), ("event_id", 1)]).skip(offset).limit(limit)
        return await cursor.to_list(length=limit)

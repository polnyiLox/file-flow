from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.file import FileORM


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
            self,
            original_name: str,
            content_type: str,
            size: int,
            original_key: str,
            file_id: str,
    ) -> FileORM:
        file_orm = FileORM(
            id=file_id,
            original_name=original_name,
            content_type=content_type,
            size=size,
            original_key=original_key,
        )
        self._session.add(file_orm)
        await self._session.flush()
        return file_orm

    async def get_all(self, limit: int, offset: int) -> list[FileORM]:
        query = (select(FileORM).order_by(FileORM.created_at.desc())
                 .limit(limit).offset(offset))
        res = await self._session.execute(query)
        return list(res.scalars().all())

    async def get_by_id(self, file_id: str) -> FileORM | None:
        query = select(FileORM).where(FileORM.id == file_id)
        return await self._session.scalar(query)
    
    async def delete(self, file_orm: FileORM) -> None:
        await self._session.delete(file_orm)
        await self._session.flush()

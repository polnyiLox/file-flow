from uuid import uuid4

from dotenv import load_dotenv
load_dotenv(".env.example", override=True)

import pytest

from app.repositories.file import FileRepository


@pytest.mark.asyncio(loop_scope="session")
async def test_file_repository_roundtrip(session):
    repository = FileRepository(session)
    file_id = str(uuid4())
    file = await repository.create("photo.png", "image/png", 12, f"files/{file_id}/original.png", file_id)
    await session.commit()
    loaded = await repository.get_by_id(file_id)
    assert loaded.original_name == "photo.png"
    assert loaded.created_at is not None
    assert loaded.thumbnail_key is None
    assert any(row.id == file_id for row in await repository.get_all(10, 0))
    await repository.delete(file)
    await session.commit()
    assert await repository.get_by_id(file_id) is None

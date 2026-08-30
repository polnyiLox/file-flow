from datetime import datetime

from sqlalchemy import Enum as SqlAlchemyEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import FileStatuses

from .base import Base


class FileORM(Base):
    __tablename__ = "files"

    original_name: Mapped[str]
    content_type: Mapped[str]
    size: Mapped[int]

    original_key: Mapped[str]
    thumbnail_key: Mapped[str] = mapped_column(
        nullable=True
    )

    status: Mapped[FileStatuses] = mapped_column(
        SqlAlchemyEnum(FileStatuses),
        default=FileStatuses.UPLOADED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
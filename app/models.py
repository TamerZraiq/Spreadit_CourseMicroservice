from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.ext.mutable import MutableList

class Base(DeclarativeBase):
    pass

class CourseDB(Base):
    __tablename__ = "course"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    course_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    course_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    enrolled_users: Mapped[list[int]] = mapped_column(MutableList.as_mutable(JSON), default=list)

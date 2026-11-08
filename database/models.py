from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()


class ReviewStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    ERROR = "error"


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    media_group_id = Column(String, unique=True, nullable=False)
    text = Column(Text, nullable=True)
    photos = Column(Text, nullable=False)  # JSON array of file_ids
    scheduled_at = Column(DateTime, nullable=False)
    published_at = Column(DateTime, nullable=True)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.SCHEDULED)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Birthday(Base):
    __tablename__ = "birthdays"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)  # birthday date
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    deadline = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Pill(Base):
    __tablename__ = "pills"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    reminder_time = Column(String, nullable=False)  # HH:MM format
    days_of_week = Column(String, nullable=False)  # JSON array of days (0-6, 0=Monday)
    is_indefinite = Column(Boolean, default=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PillLog(Base):
    __tablename__ = "pill_logs"

    id = Column(Integer, primary_key=True)
    pill_id = Column(Integer, ForeignKey("pills.id"), nullable=False)
    taken_at = Column(DateTime, default=datetime.utcnow)
    is_taken = Column(Boolean, default=True)
    pill = relationship("Pill", backref="logs")


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)  # Telegram ID
    birthdays_notification = Column(Boolean, default=True)
    tasks_notification = Column(Boolean, default=True)
    pills_notification = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

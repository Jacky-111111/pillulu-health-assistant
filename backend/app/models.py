"""SQLAlchemy models for Pillulu Health Assistant."""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    height_cm = Column(Integer, nullable=True)
    weight_kg = Column(Integer, nullable=True)
    region = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    meds = relationship("Med", back_populates="user", cascade="all, delete-orphan")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(32), nullable=False)  # "time_to_take" | "low_stock"
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)


class Med(Base):
    __tablename__ = "meds"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # nullable for migration
    name = Column(String(255), nullable=False)
    purpose = Column(String(500), nullable=True)
    dosage_notes = Column(Text, nullable=True)
    adult_dosage_guidance = Column(Text, nullable=True)
    stock_count = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_low_stock_sent_at = Column(Date, nullable=True)  # dedupe daily low-stock emails

    user = relationship("User", back_populates="meds")
    schedules = relationship("Schedule", back_populates="med", cascade="all, delete-orphan")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    med_id = Column(Integer, ForeignKey("meds.id"), nullable=False)
    time_of_day = Column(String(5), nullable=False)  # "08:30" 24h format
    timezone = Column(String(64), default="America/New_York")
    days_of_week = Column(String(64), default="daily")  # "mon,tue,wed" or "daily"
    enabled = Column(Boolean, default=True)
    last_reminder_sent_at = Column(DateTime, nullable=True)  # dedupe time-to-take reminders

    med = relationship("Med", back_populates="schedules")

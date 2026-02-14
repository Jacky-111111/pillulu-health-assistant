"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# --- Medication Search (OpenFDA) ---
class MedSearchResult(BaseModel):
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    route: Optional[str] = None
    substance_name: Optional[str] = None
    warnings_snippet: Optional[str] = None


# --- AI Ask ---
class AIAskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    context_med_name: Optional[str] = Field(None, max_length=255)


class AIAskResponse(BaseModel):
    answer: str
    disclaimer: str


# --- Pillbox Meds ---
class MedCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    purpose: Optional[str] = Field(None, max_length=500)
    dosage_notes: Optional[str] = Field(None, max_length=2000)
    stock_count: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)


class MedUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    purpose: Optional[str] = Field(None, max_length=500)
    dosage_notes: Optional[str] = Field(None, max_length=2000)
    adult_dosage_guidance: Optional[str] = Field(None, max_length=2000)
    stock_count: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)


class ScheduleSchema(BaseModel):
    id: int
    med_id: int
    time_of_day: str
    timezone: str
    days_of_week: str
    enabled: bool

    class Config:
        from_attributes = True


class MedResponse(BaseModel):
    id: int
    name: str
    purpose: Optional[str] = None
    dosage_notes: Optional[str] = None
    adult_dosage_guidance: Optional[str] = None
    stock_count: int
    low_stock_threshold: int
    created_at: datetime
    schedules: List[ScheduleSchema] = []

    class Config:
        from_attributes = True


# --- Schedule CRUD ---
class ScheduleCreate(BaseModel):
    time_of_day: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # "08:30"
    timezone: str = Field(default="America/New_York", max_length=64)
    days_of_week: str = Field(default="daily", max_length=64)
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    time_of_day: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    timezone: Optional[str] = Field(None, max_length=64)
    days_of_week: Optional[str] = Field(None, max_length=64)
    enabled: Optional[bool] = None


# --- User / Email Settings ---
class UserEmailUpdate(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)


# --- Cron ---
class CronSecretBody(BaseModel):
    secret: Optional[str] = None

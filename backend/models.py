"""Pydantic models for the Daily Action-to-Impact Coach API."""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ActionCategory(str, Enum):
    """Categories of user actions."""
    MOBILITY = "mobility"
    PURCHASE = "purchase"
    HOME_ENERGY = "home_energy"


class TimeOfDay(str, Enum):
    """Time of day for energy consumption tracking."""
    PEAK = "peak"
    OFF_PEAK = "off_peak"
    STANDARD = "standard"


class ActionLogCreate(BaseModel):
    """Schema for creating a new action log entry."""
    category: ActionCategory
    item: str = Field(..., min_length=1, description="Item identifier from factor tables")
    amount: float = Field(..., gt=0, description="Amount (km, kWh, count, etc.)")
    subcategory: Optional[str] = Field(None, description="Optional subcategory for purchases")
    time_of_day: Optional[TimeOfDay] = Field(TimeOfDay.STANDARD, description="Time of day for energy tracking")
    location: Optional[str] = Field(None, description="Optional location (district/dong)")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")

    @field_validator('item')
    @classmethod
    def lowercase_item(cls, v: str) -> str:
        return v.lower().strip()


class ActionLogResponse(BaseModel):
    """Schema for action log response with calculated impact."""
    id: int
    date: date
    category: ActionCategory
    item: str
    amount: float
    subcategory: Optional[str]
    time_of_day: Optional[str] = None  # Changed to str for flexibility
    location: Optional[str]
    notes: Optional[str]
    co2e_kg: float
    water_l: float
    created_at: Optional[datetime] = None  # Made optional for flexibility


class ImpactSummary(BaseModel):
    """Daily impact summary."""
    date: date
    total_co2e_kg: float
    total_water_l: float
    breakdown_by_category: dict[str, dict]
    top_contributors: List[dict]
    action_count: int


class WeeklyTrend(BaseModel):
    """Weekly trend data."""
    dates: List[date]
    co2e_values: List[float]
    water_values: List[float]
    daily_averages: dict


class Recommendation(BaseModel):
    """Single recommendation for next action."""
    priority: int = Field(..., ge=1, le=3)
    category: ActionCategory
    action: str
    rationale: str
    estimated_savings_co2e_kg: float
    estimated_savings_water_l: float
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")


class DailyCoachResponse(BaseModel):
    """Complete daily coaching response."""
    date: date
    summary: str
    impact_summary: ImpactSummary
    recommendations: List[Recommendation]
    streak_days: int = Field(0, description="Consecutive days of logging")


class ActionLogBulkCreate(BaseModel):
    """Schema for bulk creating action logs."""
    actions: List[ActionLogCreate]


class FactorInfo(BaseModel):
    """Information about a single emission/product factor."""
    item: str
    category: str
    subcategory: Optional[str]
    co2e_per_unit: float
    water_per_unit: float
    unit: str
    description: str


class FactorListResponse(BaseModel):
    """Response containing available factors."""
    mobility: List[FactorInfo]
    purchase: List[FactorInfo]
    home_energy: List[FactorInfo]


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str

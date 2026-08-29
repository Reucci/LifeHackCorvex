# Drop into LifeHackCorvex: backend/energy.py
#
# Converts a device's wattage + electricity rate (both supplied by the
# frontend) into energy used and cost, per day and per month.
#
# calculate_energy_consumption() has no FastAPI/pydantic dependency, so it
# stays importable on its own (scripts, tests, other routes) even without
# the web framework. POST /energy/estimate below is the thin HTTP wrapper
# the frontend actually calls.

from dataclasses import asdict, dataclass

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


@dataclass
class EnergyEstimate:
    daily_kwh: float
    daily_cost_sgd: float
    monthly_kwh: float
    monthly_cost_sgd: float


def calculate_energy_consumption(
    wattage: float,
    hours_per_day: float,
    cost_per_kwh: float,
    days_per_month: float = 30,
) -> EnergyEstimate:
    """Energy used and cost, per day and per month, for a device running at
    a constant `wattage` for `hours_per_day` hours.

    :param wattage: device power draw in watts (W)
    :param hours_per_day: hours the device runs per day (0-24)
    :param cost_per_kwh: electricity rate in Singapore dollars per kWh
    :param days_per_month: days to project the monthly figure over (default 30)
    """
    if wattage < 0:
        raise ValueError("wattage must be >= 0")
    if not 0 <= hours_per_day <= 24:
        raise ValueError("hours_per_day must be between 0 and 24")
    if cost_per_kwh < 0:
        raise ValueError("cost_per_kwh must be >= 0")
    if days_per_month <= 0:
        raise ValueError("days_per_month must be > 0")

    daily_kwh = (wattage * hours_per_day) / 1000
    daily_cost_sgd = daily_kwh * cost_per_kwh
    monthly_kwh = daily_kwh * days_per_month
    monthly_cost_sgd = monthly_kwh * cost_per_kwh

    return EnergyEstimate(
        daily_kwh=round(daily_kwh, 4),
        daily_cost_sgd=round(daily_cost_sgd, 2),
        monthly_kwh=round(monthly_kwh, 4),
        monthly_cost_sgd=round(monthly_cost_sgd, 2),
    )


class EnergyRequest(BaseModel):
    wattage: float = Field(gt=0, description="Device power draw in watts (W)")
    hours_per_day: float = Field(ge=0, le=24, description="Hours the device runs per day")
    cost_per_kwh: float = Field(gt=0, description="Electricity rate in SGD per kWh")
    days_per_month: float = Field(default=30, gt=0)


class EnergyResponse(BaseModel):
    daily_kwh: float
    daily_cost_sgd: float
    monthly_kwh: float
    monthly_cost_sgd: float


@router.post("/energy/estimate", response_model=EnergyResponse)
def estimate_energy(payload: EnergyRequest):
    estimate = calculate_energy_consumption(
        wattage=payload.wattage,
        hours_per_day=payload.hours_per_day,
        cost_per_kwh=payload.cost_per_kwh,
        days_per_month=payload.days_per_month,
    )
    return EnergyResponse(**asdict(estimate))

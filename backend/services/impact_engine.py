"""
Impact Engine - Calculates environmental impact from user actions.

This module is responsible for:
1. Loading emission/product factor tables
2. Calculating CO2e and water footprint for actions
3. Aggregating impacts by category and time period
"""

import json
from pathlib import Path
from typing import Optional, Tuple
from functools import lru_cache

# Factor data directory
DATA_DIR = Path(__file__).parent.parent / "data"


class FactorNotFoundError(Exception):
    """Raised when a factor is not found in the tables."""
    pass


@lru_cache(maxsize=1)
def load_emission_factors() -> dict:
    """Load emission factors from JSON file (cached)."""
    factor_file = DATA_DIR / "emission_factors.json"
    with open(factor_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_product_factors() -> dict:
    """Load product factors from JSON file (cached)."""
    factor_file = DATA_DIR / "product_factors.json"
    with open(factor_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_factor(category: str, item: str, subcategory: Optional[str] = None) -> dict:
    """
    Get the factor for a specific item.

    Args:
        category: 'mobility', 'purchase', or 'home_energy'
        item: The specific item identifier
        subcategory: For purchases, the subcategory (food, fashion, etc.)

    Returns:
        Dict containing co2e and water factors

    Raises:
        FactorNotFoundError: If the item is not found
    """
    item = item.lower().strip()

    if category == "mobility":
        factors = load_emission_factors()
        if item in factors.get("mobility", {}):
            factor_data = factors["mobility"][item]
            return {
                "co2e_per_unit": factor_data.get("co2e_kg_per_km", 0),
                "water_per_unit": factor_data.get("water_l_per_km", 0),
                "unit": "km",
                "description": factor_data.get("description", "")
            }

    elif category == "home_energy":
        factors = load_emission_factors()
        if item in factors.get("home_energy", {}):
            factor_data = factors["home_energy"][item]
            return {
                "co2e_per_unit": factor_data.get("co2e_kg_per_unit", 0),
                "water_per_unit": 0,  # Water not typically tracked for energy
                "unit": factor_data.get("unit", "unit"),
                "description": factor_data.get("description", "")
            }

    elif category == "purchase":
        factors = load_product_factors()
        purchase_data = factors.get("purchase", {})

        # If subcategory provided, search there first
        if subcategory and subcategory in purchase_data:
            if item in purchase_data[subcategory]:
                factor_data = purchase_data[subcategory][item]
                return {
                    "co2e_per_unit": factor_data.get("co2e_kg_per_unit", 0),
                    "water_per_unit": factor_data.get("water_l_per_unit", 0),
                    "unit": factor_data.get("unit", "unit"),
                    "description": factor_data.get("description", "")
                }

        # Search all subcategories
        for subcat, items in purchase_data.items():
            if subcat == "metadata":
                continue
            if item in items:
                factor_data = items[item]
                return {
                    "co2e_per_unit": factor_data.get("co2e_kg_per_unit", 0),
                    "water_per_unit": factor_data.get("water_l_per_unit", 0),
                    "unit": factor_data.get("unit", "unit"),
                    "description": factor_data.get("description", "")
                }

    raise FactorNotFoundError(f"Factor not found for category='{category}', item='{item}'")


def calculate_impact(
    category: str,
    item: str,
    amount: float,
    subcategory: Optional[str] = None,
    time_of_day: Optional[str] = None
) -> Tuple[float, float]:
    """
    Calculate the environmental impact of an action.

    Args:
        category: 'mobility', 'purchase', or 'home_energy'
        item: The specific item identifier
        amount: The quantity (km, kWh, count, etc.)
        subcategory: For purchases, the subcategory
        time_of_day: For energy, 'peak', 'off_peak', or 'standard'

    Returns:
        Tuple of (co2e_kg, water_l)
    """
    # Handle time-of-day variants for electricity
    if category == "home_energy" and item == "electricity_kwh" and time_of_day:
        if time_of_day == "peak":
            item = "electricity_kwh_peak"
        elif time_of_day == "off_peak":
            item = "electricity_kwh_offpeak"

    factor = get_factor(category, item, subcategory)

    co2e_kg = factor["co2e_per_unit"] * amount
    water_l = factor["water_per_unit"] * amount

    return round(co2e_kg, 4), round(water_l, 2)


def get_all_factors() -> dict:
    """Get all available factors organized by category."""
    emission_factors = load_emission_factors()
    product_factors = load_product_factors()

    result = {
        "mobility": [],
        "home_energy": [],
        "purchase": []
    }

    # Mobility factors
    for item, data in emission_factors.get("mobility", {}).items():
        result["mobility"].append({
            "item": item,
            "category": "mobility",
            "subcategory": None,
            "co2e_per_unit": data.get("co2e_kg_per_km", 0),
            "water_per_unit": data.get("water_l_per_km", 0),
            "unit": "km",
            "description": data.get("description", "")
        })

    # Home energy factors
    for item, data in emission_factors.get("home_energy", {}).items():
        result["home_energy"].append({
            "item": item,
            "category": "home_energy",
            "subcategory": None,
            "co2e_per_unit": data.get("co2e_kg_per_unit", 0),
            "water_per_unit": 0,
            "unit": data.get("unit", "unit"),
            "description": data.get("description", "")
        })

    # Purchase factors
    for subcategory, items in product_factors.get("purchase", {}).items():
        if subcategory == "metadata":
            continue
        for item, data in items.items():
            result["purchase"].append({
                "item": item,
                "category": "purchase",
                "subcategory": subcategory,
                "co2e_per_unit": data.get("co2e_kg_per_unit", 0),
                "water_per_unit": data.get("water_l_per_unit", 0),
                "unit": data.get("unit", "unit"),
                "description": data.get("description", "")
            })

    return result


def get_category_benchmark(category: str) -> dict:
    """
    Get benchmark values for comparison.

    Returns average daily impacts for a typical person in Korea.
    """
    benchmarks = {
        "mobility": {
            "avg_daily_co2e_kg": 3.5,
            "avg_daily_water_l": 8.0,
            "description": "Average Korean daily mobility footprint"
        },
        "purchase": {
            "avg_daily_co2e_kg": 4.2,
            "avg_daily_water_l": 2500,
            "description": "Average Korean daily consumption footprint"
        },
        "home_energy": {
            "avg_daily_co2e_kg": 2.8,
            "avg_daily_water_l": 0,
            "description": "Average Korean household daily energy footprint (per person)"
        }
    }
    return benchmarks.get(category, {"avg_daily_co2e_kg": 0, "avg_daily_water_l": 0})


def compare_to_benchmark(category: str, co2e_kg: float, water_l: float) -> dict:
    """Compare actual impact to benchmark."""
    benchmark = get_category_benchmark(category)

    co2e_benchmark = benchmark.get("avg_daily_co2e_kg", 1)
    water_benchmark = benchmark.get("avg_daily_water_l", 1)

    co2e_ratio = co2e_kg / co2e_benchmark if co2e_benchmark > 0 else 0
    water_ratio = water_l / water_benchmark if water_benchmark > 0 else 0

    return {
        "co2e_vs_avg_percent": round((co2e_ratio - 1) * 100, 1),
        "water_vs_avg_percent": round((water_ratio - 1) * 100, 1),
        "co2e_benchmark_kg": co2e_benchmark,
        "water_benchmark_l": water_benchmark
    }


def clear_factor_cache() -> None:
    """Clear the cached factor data (useful for testing or reloading)."""
    load_emission_factors.cache_clear()
    load_product_factors.cache_clear()

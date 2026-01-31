"""
Recommendation Engine - Generates actionable next-step recommendations.

This module is responsible for:
1. Analyzing daily impact patterns
2. Identifying high-impact areas
3. Generating personalized recommendations with estimated savings
"""

from datetime import date
from typing import List, Optional
from dataclasses import dataclass

from .impact_engine import get_factor, get_all_factors, FactorNotFoundError


@dataclass
class RecommendationRule:
    """A single recommendation rule."""
    category: str
    trigger_item: str
    action: str
    alternative_item: Optional[str]
    rationale: str
    difficulty: str  # easy, medium, hard


# Predefined recommendation rules
RECOMMENDATION_RULES: List[RecommendationRule] = [
    # Mobility recommendations
    RecommendationRule(
        category="mobility",
        trigger_item="taxi_ice",
        action="Switch to EV taxi for your next ride",
        alternative_item="taxi_ev",
        rationale="EV taxis produce 76% less CO2 than gasoline taxis",
        difficulty="easy"
    ),
    RecommendationRule(
        category="mobility",
        trigger_item="taxi_ice",
        action="Use public transit for trips under 5km",
        alternative_item="subway",
        rationale="Subway produces 83% less CO2 per km than taxi",
        difficulty="medium"
    ),
    RecommendationRule(
        category="mobility",
        trigger_item="personal_car_gasoline",
        action="Consider carpooling or public transit tomorrow",
        alternative_item="bus",
        rationale="Bus travel reduces your per-km emissions by 54%",
        difficulty="medium"
    ),
    RecommendationRule(
        category="mobility",
        trigger_item="personal_car_gasoline",
        action="Try walking or cycling for short trips under 3km",
        alternative_item="bicycle",
        rationale="Zero emissions and health benefits",
        difficulty="easy"
    ),
    RecommendationRule(
        category="mobility",
        trigger_item="domestic_flight",
        action="Consider KTX for domestic travel when possible",
        alternative_item="train_ktx",
        rationale="High-speed rail produces 89% less CO2 than flying",
        difficulty="medium"
    ),

    # Food recommendations
    RecommendationRule(
        category="purchase",
        trigger_item="beef_meal",
        action="Try chicken or fish for one meal tomorrow",
        alternative_item="chicken_meal",
        rationale="Chicken produces 83% less CO2 and uses 77% less water than beef",
        difficulty="easy"
    ),
    RecommendationRule(
        category="purchase",
        trigger_item="beef_meal",
        action="Explore a vegetarian meal option",
        alternative_item="vegetarian_meal",
        rationale="Vegetarian meals produce 94% less CO2 than beef",
        difficulty="medium"
    ),
    RecommendationRule(
        category="purchase",
        trigger_item="coffee",
        action="Bring a reusable cup for your coffee",
        alternative_item=None,
        rationale="Reduces packaging waste and often gets you a discount",
        difficulty="easy"
    ),
    RecommendationRule(
        category="purchase",
        trigger_item="milk_liter",
        action="Try plant-based milk alternatives",
        alternative_item="oat_milk_liter",
        rationale="Oat milk produces 53% less CO2 and 92% less water than dairy",
        difficulty="easy"
    ),

    # Fashion recommendations
    RecommendationRule(
        category="purchase",
        trigger_item="tshirt_fastfashion",
        action="Consider secondhand or sustainable options next time",
        alternative_item="tshirt_secondhand",
        rationale="Secondhand clothing reduces impact by 91%",
        difficulty="medium"
    ),
    RecommendationRule(
        category="purchase",
        trigger_item="jeans_fastfashion",
        action="Postpone your next jeans purchase and explore secondhand",
        alternative_item="jeans_secondhand",
        rationale="Secondhand jeans save 95% of CO2 and water",
        difficulty="medium"
    ),
    RecommendationRule(
        category="purchase",
        trigger_item="sneakers_new",
        action="Check for refurbished or secondhand options",
        alternative_item="sneakers_secondhand",
        rationale="Secondhand shoes reduce impact by 90%",
        difficulty="medium"
    ),

    # Electronics recommendations
    RecommendationRule(
        category="purchase",
        trigger_item="smartphone_new",
        action="Consider refurbished phones for your next upgrade",
        alternative_item="smartphone_refurbished",
        rationale="Refurbished phones use 79% less resources",
        difficulty="easy"
    ),
    RecommendationRule(
        category="purchase",
        trigger_item="laptop_new",
        action="Extend your laptop's life or buy refurbished",
        alternative_item="laptop_refurbished",
        rationale="Refurbished laptops reduce impact by 80%",
        difficulty="medium"
    ),

    # Household recommendations
    RecommendationRule(
        category="purchase",
        trigger_item="plastic_bag",
        action="Bring reusable bags for shopping",
        alternative_item="reusable_bag",
        rationale="Reusable bags reduce impact by 94% per use",
        difficulty="easy"
    ),
    RecommendationRule(
        category="purchase",
        trigger_item="bottled_water_500ml",
        action="Use a reusable water bottle",
        alternative_item="tap_water_500ml",
        rationale="Tap water in reusable bottles reduces impact by 99%",
        difficulty="easy"
    ),

    # Home energy recommendations
    RecommendationRule(
        category="home_energy",
        trigger_item="electricity_kwh",
        action="Shift high-power activities to off-peak hours",
        alternative_item="electricity_kwh_offpeak",
        rationale="Off-peak electricity has 17% lower carbon intensity",
        difficulty="medium"
    ),
    RecommendationRule(
        category="home_energy",
        trigger_item="electricity_kwh_peak",
        action="Reduce peak-hour electricity usage tomorrow",
        alternative_item="electricity_kwh_offpeak",
        rationale="Peak hours have 31% higher carbon intensity",
        difficulty="medium"
    ),
    RecommendationRule(
        category="home_energy",
        trigger_item="natural_gas_m3",
        action="Lower heating by 1-2 degrees and wear layers",
        alternative_item=None,
        rationale="Each degree reduction saves about 7% of heating energy",
        difficulty="easy"
    ),
]


def calculate_savings(trigger_item: str, alternative_item: str, category: str, amount: float = 1.0) -> dict:
    """Calculate potential savings from switching to an alternative."""
    try:
        trigger_factor = get_factor(category, trigger_item)
        alt_factor = get_factor(category, alternative_item)

        co2e_savings = (trigger_factor["co2e_per_unit"] - alt_factor["co2e_per_unit"]) * amount
        water_savings = (trigger_factor["water_per_unit"] - alt_factor["water_per_unit"]) * amount

        return {
            "co2e_kg": round(max(0, co2e_savings), 4),
            "water_l": round(max(0, water_savings), 2)
        }
    except FactorNotFoundError:
        return {"co2e_kg": 0, "water_l": 0}


def get_recommendations(
    daily_actions: List[dict],
    max_recommendations: int = 3
) -> List[dict]:
    """
    Generate recommendations based on daily actions.

    Args:
        daily_actions: List of action dicts with category, item, amount, co2e_kg
        max_recommendations: Maximum number of recommendations to return

    Returns:
        List of recommendation dicts sorted by potential impact
    """
    if not daily_actions:
        return get_default_recommendations(max_recommendations)

    # Find matching rules and calculate potential savings
    matched_recommendations = []

    # Group actions by category and item
    action_totals = {}
    for action in daily_actions:
        key = (action["category"], action["item"])
        if key not in action_totals:
            action_totals[key] = {"amount": 0, "co2e_kg": 0}
        action_totals[key]["amount"] += action.get("amount", 1)
        action_totals[key]["co2e_kg"] += action.get("co2e_kg", 0)

    # Find applicable rules
    seen_actions = set()
    for (category, item), totals in action_totals.items():
        for rule in RECOMMENDATION_RULES:
            if rule.category == category and rule.trigger_item == item:
                # Avoid duplicate recommendations for same action
                action_key = f"{rule.category}:{rule.action}"
                if action_key in seen_actions:
                    continue
                seen_actions.add(action_key)

                # Calculate savings
                if rule.alternative_item:
                    savings = calculate_savings(
                        rule.trigger_item,
                        rule.alternative_item,
                        category,
                        totals["amount"]
                    )
                else:
                    # Estimate 20% reduction for behavioral changes
                    savings = {
                        "co2e_kg": round(totals["co2e_kg"] * 0.2, 4),
                        "water_l": 0
                    }

                matched_recommendations.append({
                    "priority": 0,  # Will be set after sorting
                    "category": category,
                    "action": rule.action,
                    "rationale": rule.rationale,
                    "estimated_savings_co2e_kg": savings["co2e_kg"],
                    "estimated_savings_water_l": savings["water_l"],
                    "difficulty": rule.difficulty,
                    "trigger_item": item,
                    "trigger_amount": totals["amount"]
                })

    # Sort by potential CO2e savings (descending)
    matched_recommendations.sort(
        key=lambda r: r["estimated_savings_co2e_kg"],
        reverse=True
    )

    # Assign priorities and limit
    result = []
    for i, rec in enumerate(matched_recommendations[:max_recommendations]):
        rec["priority"] = i + 1
        result.append(rec)

    # If we don't have enough recommendations, add defaults
    if len(result) < max_recommendations:
        defaults = get_default_recommendations(max_recommendations - len(result))
        for i, rec in enumerate(defaults):
            rec["priority"] = len(result) + i + 1
            result.append(rec)

    return result


def get_default_recommendations(count: int = 3) -> List[dict]:
    """Get default recommendations when no specific triggers are found."""
    defaults = [
        {
            "priority": 1,
            "category": "mobility",
            "action": "Try walking or cycling for one trip today",
            "rationale": "Zero-emission transport improves health and reduces carbon footprint",
            "estimated_savings_co2e_kg": 0.5,
            "estimated_savings_water_l": 0,
            "difficulty": "easy"
        },
        {
            "priority": 2,
            "category": "purchase",
            "action": "Choose a plant-based meal option today",
            "rationale": "Plant-based meals typically have 50-80% lower carbon footprint",
            "estimated_savings_co2e_kg": 3.0,
            "estimated_savings_water_l": 1000,
            "difficulty": "easy"
        },
        {
            "priority": 3,
            "category": "home_energy",
            "action": "Turn off unused lights and appliances",
            "rationale": "Standby power can account for 5-10% of home energy use",
            "estimated_savings_co2e_kg": 0.2,
            "estimated_savings_water_l": 0,
            "difficulty": "easy"
        },
        {
            "priority": 4,
            "category": "purchase",
            "action": "Bring a reusable bag for your next shopping trip",
            "rationale": "Single-use plastics contribute to pollution and emissions",
            "estimated_savings_co2e_kg": 0.03,
            "estimated_savings_water_l": 0.5,
            "difficulty": "easy"
        },
        {
            "priority": 5,
            "category": "mobility",
            "action": "Plan your errands to combine trips",
            "rationale": "Fewer trips mean less fuel and lower emissions",
            "estimated_savings_co2e_kg": 1.0,
            "estimated_savings_water_l": 0,
            "difficulty": "easy"
        }
    ]
    return defaults[:count]


def generate_daily_summary(
    total_co2e_kg: float,
    total_water_l: float,
    top_contributors: List[dict]
) -> str:
    """Generate a human-readable daily summary."""
    if total_co2e_kg == 0:
        return "No actions logged today. Start tracking to understand your environmental impact!"

    # Determine impact level
    if total_co2e_kg < 2:
        level = "low"
        emoji_desc = "Great job"
    elif total_co2e_kg < 5:
        level = "moderate"
        emoji_desc = "Room for improvement"
    elif total_co2e_kg < 10:
        level = "high"
        emoji_desc = "Consider alternatives"
    else:
        level = "very high"
        emoji_desc = "Significant impact day"

    # Build summary
    summary_parts = [
        f"Today's impact: {total_co2e_kg:.2f} kg CO2e ({level}). {emoji_desc}."
    ]

    if total_water_l > 0:
        summary_parts.append(f"Water footprint: {total_water_l:.0f} L.")

    if top_contributors:
        top_item = top_contributors[0]
        summary_parts.append(
            f"Biggest contributor: {top_item['item'].replace('_', ' ')} "
            f"({top_item['co2e_kg']:.2f} kg CO2e)."
        )

    return " ".join(summary_parts)


def get_weekly_insight(weekly_data: List[dict]) -> str:
    """Generate insight from weekly trend data."""
    if not weekly_data or len(weekly_data) < 2:
        return "Keep logging to see your weekly trends!"

    co2e_values = [d.get("total_co2e", 0) for d in weekly_data]
    avg_co2e = sum(co2e_values) / len(co2e_values)

    if len(co2e_values) >= 2:
        recent = co2e_values[-1]
        previous = co2e_values[-2]

        if previous > 0:
            change_pct = ((recent - previous) / previous) * 100

            if change_pct < -10:
                return f"Excellent! Your emissions dropped {abs(change_pct):.0f}% compared to yesterday."
            elif change_pct > 10:
                return f"Your emissions increased {change_pct:.0f}% compared to yesterday. Check your top contributors."
            else:
                return f"Your emissions are stable. Weekly average: {avg_co2e:.1f} kg CO2e/day."

    return f"Weekly average: {avg_co2e:.1f} kg CO2e/day."

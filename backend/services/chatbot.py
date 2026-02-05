"""
Chatbot Parser Service

Parses natural language input into structured action data.
Uses pattern matching and keyword extraction for MVP.
"""

import re
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class ParsedAction:
    """Represents a parsed action from natural language."""
    category: str
    item: str
    amount: float
    confidence: float
    original_text: str


# Keyword mappings for natural language parsing
MOBILITY_KEYWORDS = {
    # Korean keywords
    "택시": ("taxi_ice", "mobility"),
    "전기택시": ("taxi_ev", "mobility"),
    "버스": ("bus", "mobility"),
    "지하철": ("subway", "mobility"),
    "자전거": ("bicycle", "mobility"),
    "걸어": ("walking", "mobility"),
    "도보": ("walking", "mobility"),
    "차": ("car_gasoline", "mobility"),
    "자동차": ("car_gasoline", "mobility"),
    "전기차": ("car_ev", "mobility"),
    "오토바이": ("motorcycle", "mobility"),
    "킥보드": ("escooter", "mobility"),
    # English keywords
    "taxi": ("taxi_ice", "mobility"),
    "uber": ("taxi_ice", "mobility"),
    "bus": ("bus", "mobility"),
    "subway": ("subway", "mobility"),
    "metro": ("subway", "mobility"),
    "bike": ("bicycle", "mobility"),
    "bicycle": ("bicycle", "mobility"),
    "walk": ("walking", "mobility"),
    "car": ("car_gasoline", "mobility"),
    "drive": ("car_gasoline", "mobility"),
}

FOOD_KEYWORDS = {
    # Korean keywords
    "소고기": ("beef_meal", "purchase"),
    "쇠고기": ("beef_meal", "purchase"),
    "스테이크": ("beef_meal", "purchase"),
    "돼지고기": ("pork_meal", "purchase"),
    "삼겹살": ("pork_meal", "purchase"),
    "닭고기": ("chicken_meal", "purchase"),
    "치킨": ("chicken_meal", "purchase"),
    "생선": ("fish_meal", "purchase"),
    "채식": ("vegetarian_meal", "purchase"),
    "비건": ("vegan_meal", "purchase"),
    "커피": ("coffee", "purchase"),
    "아메리카노": ("coffee", "purchase"),
    "라떼": ("coffee", "purchase"),
    "우유": ("milk_liter", "purchase"),
    # English keywords
    "beef": ("beef_meal", "purchase"),
    "steak": ("beef_meal", "purchase"),
    "pork": ("pork_meal", "purchase"),
    "chicken": ("chicken_meal", "purchase"),
    "fish": ("fish_meal", "purchase"),
    "vegetarian": ("vegetarian_meal", "purchase"),
    "vegan": ("vegan_meal", "purchase"),
    "coffee": ("coffee", "purchase"),
    "milk": ("milk_liter", "purchase"),
}

FASHION_KEYWORDS = {
    # Korean keywords
    "티셔츠": ("tshirt_fastfashion", "purchase"),
    "옷": ("tshirt_fastfashion", "purchase"),
    "청바지": ("jeans_fastfashion", "purchase"),
    "바지": ("jeans_fastfashion", "purchase"),
    "신발": ("sneakers_new", "purchase"),
    "운동화": ("sneakers_new", "purchase"),
    "중고": ("tshirt_secondhand", "purchase"),
    # English keywords
    "tshirt": ("tshirt_fastfashion", "purchase"),
    "t-shirt": ("tshirt_fastfashion", "purchase"),
    "shirt": ("tshirt_fastfashion", "purchase"),
    "jeans": ("jeans_fastfashion", "purchase"),
    "pants": ("jeans_fastfashion", "purchase"),
    "shoes": ("sneakers_new", "purchase"),
    "sneakers": ("sneakers_new", "purchase"),
    "secondhand": ("tshirt_secondhand", "purchase"),
    "used": ("tshirt_secondhand", "purchase"),
}

ENERGY_KEYWORDS = {
    # Korean keywords
    "전기": ("electricity_kwh", "home_energy"),
    "에어컨": ("electricity_kwh", "home_energy"),
    "냉방": ("electricity_kwh", "home_energy"),
    "난방": ("natural_gas_m3", "home_energy"),
    "가스": ("natural_gas_m3", "home_energy"),
    "보일러": ("natural_gas_m3", "home_energy"),
    "샤워": ("hot_water_shower", "home_energy"),
    # English keywords
    "electricity": ("electricity_kwh", "home_energy"),
    "electric": ("electricity_kwh", "home_energy"),
    "ac": ("electricity_kwh", "home_energy"),
    "air conditioning": ("electricity_kwh", "home_energy"),
    "heating": ("natural_gas_m3", "home_energy"),
    "gas": ("natural_gas_m3", "home_energy"),
    "shower": ("hot_water_shower", "home_energy"),
}

# Combine all keywords
ALL_KEYWORDS = {
    **MOBILITY_KEYWORDS,
    **FOOD_KEYWORDS,
    **FASHION_KEYWORDS,
    **ENERGY_KEYWORDS,
}

# Number patterns for Korean and English
NUMBER_PATTERNS = [
    # Korean numbers with units
    r'(\d+(?:\.\d+)?)\s*(?:km|킬로|킬로미터)',
    r'(\d+(?:\.\d+)?)\s*(?:번|개|잔|벌|켤레|인분)',
    r'(\d+(?:\.\d+)?)\s*(?:kWh|킬로와트)',
    r'(\d+(?:\.\d+)?)\s*(?:시간|분)',
    # General numbers
    r'(\d+(?:\.\d+)?)',
]


def extract_number(text: str) -> float:
    """Extract the first number from text."""
    for pattern in NUMBER_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    return 1.0  # Default to 1 if no number found


def parse_message(message: str) -> List[ParsedAction]:
    """
    Parse a natural language message into structured actions.

    Examples:
        "오늘 택시로 5km 이동했어" -> [ParsedAction(mobility, taxi_ice, 5)]
        "점심에 스테이크 먹었어" -> [ParsedAction(purchase, beef_meal, 1)]
        "커피 2잔 마셨어" -> [ParsedAction(purchase, coffee, 2)]
    """
    actions = []
    message_lower = message.lower()

    # Find all matching keywords
    found_keywords = []
    for keyword, (item, category) in ALL_KEYWORDS.items():
        if keyword in message_lower:
            # Calculate position for ordering
            pos = message_lower.index(keyword)
            found_keywords.append((pos, keyword, item, category))

    # Sort by position in message
    found_keywords.sort(key=lambda x: x[0])

    # Remove duplicates (keep first occurrence of each item)
    seen_items = set()
    unique_keywords = []
    for pos, keyword, item, category in found_keywords:
        if item not in seen_items:
            seen_items.add(item)
            unique_keywords.append((pos, keyword, item, category))

    # Extract actions
    for pos, keyword, item, category in unique_keywords:
        # Try to find number near this keyword
        # Look in a window around the keyword
        start = max(0, pos - 20)
        end = min(len(message), pos + len(keyword) + 20)
        context = message[start:end]

        amount = extract_number(context)

        # Calculate confidence based on pattern matching
        confidence = 0.8 if amount != 1.0 else 0.6

        actions.append(ParsedAction(
            category=category,
            item=item,
            amount=amount,
            confidence=confidence,
            original_text=message
        ))

    return actions


def generate_response(actions: List[ParsedAction], impact_results: List[Dict]) -> str:
    """
    Generate a natural language response based on parsed actions and their impacts.
    """
    if not actions:
        return """죄송합니다, 입력하신 내용에서 행동을 인식하지 못했습니다.

다음과 같이 말씀해 주세요:
- "오늘 택시로 5km 이동했어"
- "점심에 소고기 먹었어"
- "커피 2잔 마셨어"
- "전기 10kWh 사용했어"

어떤 활동을 하셨나요?"""

    # Build response
    lines = ["📊 **오늘의 활동 분석**\n"]

    total_co2e = 0
    total_water = 0

    for action, impact in zip(actions, impact_results):
        category_emoji = {
            "mobility": "🚗",
            "purchase": "🛒",
            "home_energy": "🏠"
        }.get(action.category, "📌")

        item_name = action.item.replace("_", " ").title()
        co2e = impact.get('co2e_kg', 0)
        water = impact.get('water_l', 0)

        total_co2e += co2e
        total_water += water

        lines.append(f"{category_emoji} **{item_name}** ({action.amount})")
        lines.append(f"   - CO₂e: {co2e:.3f} kg")
        if water > 0:
            lines.append(f"   - 물: {water:.1f} L")
        lines.append("")

    lines.append("---")
    lines.append(f"**📈 총 영향**")
    lines.append(f"- 탄소 발자국: **{total_co2e:.3f} kg CO₂e**")
    if total_water > 0:
        lines.append(f"- 물 발자국: **{total_water:.1f} L**")

    # Add context
    lines.append("")
    if total_co2e > 5:
        lines.append("💡 **팁**: 오늘 탄소 배출이 높은 편이에요. 내일은 대중교통이나 채식 식사를 고려해보세요!")
    elif total_co2e > 2:
        lines.append("💡 **팁**: 괜찮은 하루예요! 작은 변화가 큰 차이를 만들어요.")
    else:
        lines.append("🌱 **훌륭해요!** 환경을 위한 좋은 선택을 하셨네요!")

    return "\n".join(lines)


def get_chat_suggestions() -> List[str]:
    """Get example chat suggestions for the user."""
    return [
        "오늘 택시로 5km 이동했어",
        "점심에 소고기 스테이크 먹었어",
        "커피 3잔 마셨어",
        "지하철로 10km 출퇴근했어",
        "에어컨 3시간 사용했어",
        "새 티셔츠 2벌 샀어",
        "자전거로 출근했어",
        "채식 점심 먹었어",
    ]


class ChatSession:
    """Manages a chat session with history."""

    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.daily_actions: List[ParsedAction] = []
        self.daily_impacts: List[Dict] = []

    def add_message(self, role: str, content: str):
        """Add a message to history."""
        self.history.append({"role": role, "content": content})

    def add_action(self, action: ParsedAction, impact: Dict):
        """Add a parsed action and its impact."""
        self.daily_actions.append(action)
        self.daily_impacts.append(impact)

    def get_daily_summary(self) -> Dict:
        """Get summary of today's actions."""
        total_co2e = sum(i.get('co2e_kg', 0) for i in self.daily_impacts)
        total_water = sum(i.get('water_l', 0) for i in self.daily_impacts)

        return {
            "action_count": len(self.daily_actions),
            "total_co2e_kg": total_co2e,
            "total_water_l": total_water,
            "actions": [
                {
                    "item": a.item,
                    "amount": a.amount,
                    "category": a.category,
                    "co2e_kg": i.get('co2e_kg', 0),
                    "water_l": i.get('water_l', 0)
                }
                for a, i in zip(self.daily_actions, self.daily_impacts)
            ]
        }

    def clear(self):
        """Clear the session."""
        self.history = []
        self.daily_actions = []
        self.daily_impacts = []

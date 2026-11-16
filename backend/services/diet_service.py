from services.llm_service import llm_service

NUTRIENT_TARGETS = {
    "balanced": {"calories": 2000, "protein": 50, "carbs": 275, "fat": 65},
    "high_protein": {"calories": 2200, "protein": 150, "carbs": 200, "fat": 70},
    "low_carb": {"calories": 1800, "protein": 120, "carbs": 100, "fat": 80},
    "vegetarian": {"calories": 1900, "protein": 45, "carbs": 260, "fat": 60},
}


class DietService:
    def generate_meal_plan(
        self,
        preferences: dict,
        ingredients: list[str],
        meal_types: list[str],
        diet_type: str = "balanced",
    ) -> dict:
        nutrients = NUTRIENT_TARGETS.get(diet_type, NUTRIENT_TARGETS["balanced"])

        prompt = f"""Generate a personalized 1-day meal plan as JSON with this structure:
{{
  "meals": [
    {{"type": "breakfast", "name": "...", "ingredients": [...], "calories": N, "protein": N, "carbs": N, "fat": N, "recipe": "..."}}
  ],
  "total_nutrients": {{"calories": N, "protein": N, "carbs": N, "fat": N}}
}}

User preferences: {preferences}
Available ingredients: {', '.join(ingredients) if ingredients else 'any'}
Meal types requested: {', '.join(meal_types)}
Target nutrients: {nutrients}
Diet type: {diet_type}

Use only the available ingredients where possible. Return valid JSON only."""

        response = llm_service.generate(prompt, json_mode=True)

        try:
            import json
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            pass

        return self._default_meal_plan(meal_types, ingredients, nutrients)

    def _default_meal_plan(self, meal_types: list[str], ingredients: list[str], nutrients: dict) -> dict:
        meals = []
        defaults = {
            "breakfast": {
                "name": "Oatmeal with Fruits",
                "ingredients": ["oats", "banana", "honey"],
                "calories": 350, "protein": 12, "carbs": 55, "fat": 8,
                "recipe": "Cook oats with water, top with sliced banana and honey.",
            },
            "lunch": {
                "name": "Vegetable Rice Bowl",
                "ingredients": ["rice", "vegetables", "olive oil"],
                "calories": 500, "protein": 15, "carbs": 70, "fat": 18,
                "recipe": "Stir-fry vegetables, serve over steamed rice with olive oil.",
            },
            "dinner": {
                "name": "Grilled Protein with Salad",
                "ingredients": ["chicken", "lettuce", "tomato"],
                "calories": 450, "protein": 35, "carbs": 20, "fat": 22,
                "recipe": "Grill protein, serve with fresh salad.",
            },
            "snack": {
                "name": "Mixed Nuts",
                "ingredients": ["almonds", "walnuts"],
                "calories": 200, "protein": 8, "carbs": 10, "fat": 16,
                "recipe": "A handful of mixed nuts.",
            },
        }

        for meal_type in meal_types:
            template = defaults.get(meal_type, defaults["lunch"])
            if ingredients:
                template = {**template, "ingredients": ingredients[:5]}
            meals.append({"type": meal_type, **template})

        total = {
            "calories": sum(m["calories"] for m in meals),
            "protein": sum(m["protein"] for m in meals),
            "carbs": sum(m["carbs"] for m in meals),
            "fat": sum(m["fat"] for m in meals),
        }

        return {"meals": meals, "total_nutrients": total, "target_nutrients": nutrients}


diet_service = DietService()

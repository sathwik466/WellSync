from flask import Blueprint, jsonify, request

from models.database import DietPlan, db
from services.diet_service import diet_service

diet_bp = Blueprint("diet", __name__)


@diet_bp.route("/generate", methods=["POST"])
def generate_plan():
    data = request.get_json()
    preferences = data.get("preferences", {})
    ingredients = data.get("ingredients", [])
    meal_types = data.get("meal_types", ["breakfast", "lunch", "dinner"])
    diet_type = data.get("diet_type", "balanced")
    user_id = data.get("user_id")

    plan = diet_service.generate_meal_plan(preferences, ingredients, meal_types, diet_type)

    if user_id:
        record = DietPlan(user_id=user_id, preferences=preferences, meal_plan=plan)
        db.session.add(record)
        db.session.commit()
        plan["saved_id"] = record.id

    return jsonify(plan)


@diet_bp.route("/history/<int:user_id>", methods=["GET"])
def get_history(user_id):
    plans = DietPlan.query.filter_by(user_id=user_id).order_by(DietPlan.created_at.desc()).limit(10).all()
    return jsonify([
        {"id": p.id, "preferences": p.preferences, "meal_plan": p.meal_plan, "created_at": p.created_at.isoformat()}
        for p in plans
    ])

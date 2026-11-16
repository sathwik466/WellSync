from flask import Blueprint, jsonify, request

from models.database import MovieRecommendation, db
from services.movie_service import movie_service

movies_bp = Blueprint("movies", __name__)


@movies_bp.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    mood = data.get("mood", "neutral")
    user_id = data.get("user_id")

    result = movie_service.recommend(mood)

    if user_id:
        record = MovieRecommendation(user_id=user_id, mood=mood, movies=result["movies"])
        db.session.add(record)
        db.session.commit()

    return jsonify(result)


@movies_bp.route("/moods", methods=["GET"])
def get_moods():
    return jsonify(["happy", "sad", "angry", "fear", "surprise", "neutral", "disgust"])

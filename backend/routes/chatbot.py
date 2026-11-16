from flask import Blueprint, jsonify, request

from services.chatbot_service import chatbot_service

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    result = chatbot_service.chat(message, session_id)
    return jsonify(result)

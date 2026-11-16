from flask import Flask
from flask_cors import CORS

from config import Config
from models.database import db
from routes.chatbot import chatbot_bp
from routes.diet import diet_bp
from routes.movies import movies_bp
from routes.yoga import yoga_bp
from services.faiss_service import faiss_service


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)

    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
    app.register_blueprint(yoga_bp, url_prefix="/api/yoga")
    app.register_blueprint(diet_bp, url_prefix="/api/diet")
    app.register_blueprint(movies_bp, url_prefix="/api/movies")

    @app.route("/api/health")
    def health():
        return {"status": "ok", "app": "WellSync"}

    with app.app_context():
        db.create_all()
        faiss_service.load_index()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)

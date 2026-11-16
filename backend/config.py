
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy.engine import URL

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE", "wellsync")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "wellsync-chat")

    # LLM Settings (Groq / Ollama)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_API_URL = os.getenv(
        "GROQ_API_URL",
        "https://api.groq.com/openai/v1/chat/completions"
    )

    # TMDB Settings
    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
    TMDB_BASE_URL = os.getenv(
        "TMDB_BASE_URL", "https://api.themoviedb.org/3"
    )
    TMDB_IMAGE_BASE_URL = os.getenv(
        "TMDB_IMAGE_BASE_URL", "https://image.tmdb.org/t/p/w500"
    )
    TMDB_BACKDROP_BASE_URL = os.getenv(
        "TMDB_BACKDROP_BASE_URL", "https://image.tmdb.org/t/p/w780"
    )

    # Local Ollama Fallback Settings
    LLM_API_URL = os.getenv(
        "LLM_API_URL", "http://localhost:11434/api/generate"
    )
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3")

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL", "all-MiniLM-L6-v2"
    )

    FAISS_INDEX_PATH = os.path.join(
        os.path.dirname(__file__), "data", "faiss_index"
    )
    KNOWLEDGE_BASE_PATH = os.path.join(
        os.path.dirname(__file__), "data", "knowledge_base.txt"
    )

from config import Config


class PineconeService:
    def __init__(self):
        self.index = None
        self._initialized = False

    def _init_client(self):
        if self._initialized:
            return

        if not Config.PINECONE_API_KEY:
            self._initialized = True
            return

        try:
            from pinecone import Pinecone, ServerlessSpec

            pc = Pinecone(api_key=Config.PINECONE_API_KEY)
            existing = [idx.name for idx in pc.list_indexes()]

            if Config.PINECONE_INDEX_NAME not in existing:
                pc.create_index(
                    name=Config.PINECONE_INDEX_NAME,
                    dimension=384,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )

            self.index = pc.Index(Config.PINECONE_INDEX_NAME)
        except Exception:
            self.index = None

        self._initialized = True

    def store_chat(self, session_id: str, role: str, content: str, embedding: list[float]):
        self._init_client()
        if self.index is None:
            return

        vector_id = f"{session_id}_{hash(content) % 10**8}"
        self.index.upsert(
            vectors=[{
                "id": vector_id,
                "values": embedding,
                "metadata": {"session_id": session_id, "role": role, "content": content},
            }]
        )

    def get_chat_history(self, session_id: str, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        self._init_client()
        if self.index is None:
            return []

        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter={"session_id": session_id},
                include_metadata=True,
            )
            return [
                {"role": m["metadata"]["role"], "content": m["metadata"]["content"]}
                for m in results.get("matches", [])
            ]
        except Exception:
            return []


pinecone_service = PineconeService()

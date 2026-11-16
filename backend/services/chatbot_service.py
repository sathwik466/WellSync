import uuid

from services.embedding_service import encode_text
from services.faiss_service import faiss_service
from services.llm_service import llm_service
from services.pinecone_service import pinecone_service

SYSTEM_PROMPT = """You are WellSync, an insightful, compassionate, and evidence-informed mental wellness companion.

Your primary mission is to provide clear, structured, and deeply educational explanations to support the user's mental health, stress management, and emotional well-being.

Core Guidelines:
1. LEVERAGE THE KNOWLEDGE BASE: Actively draw upon the provided Knowledge Base context to explain both the 'why' (underlying physiology, neuroscience, or cognitive psychology) and the 'how' (concrete, actionable steps). When explaining techniques such as the physiological sigh, box breathing, 5-4-3-2-1 sensory grounding, CBT thought records, behavioral activation, or sleep hygiene, give clear step-by-step guidance.
2. STRUCTURE & CLARITY: Ensure your explanations are exceptionally easy to read. Use clear headings, bullet points, and numbered steps where appropriate so the user can easily absorb and practice the advice.
3. EMPATHY & VALIDATION: Acknowledge the user's emotional state with warmth, genuine empathy, and non-judgmental acceptance. Validate that their feelings are understandable human experiences.
4. SAFETY & BOUNDARIES: Never provide clinical medical diagnoses, prescribe medications, or replace professional psychiatric/psychological care. If a user expresses severe crisis, self-harm, or overwhelming despair, warmly provide crisis helpline information (e.g., 988 in the US/Canada, 111/116 123 in the UK, findahelpline.com internationally)."""


class ChatbotService:
    def chat(self, message: str, session_id: str | None = None) -> dict:
        session_id = session_id or str(uuid.uuid4())

        query_embedding = encode_text(message)

        # Retrieve relevant context from the detailed FAISS knowledge base
        kb_context = faiss_service.search(message, top_k=4)
        chat_history = pinecone_service.get_chat_history(session_id, query_embedding, top_k=5)

        context_parts = []
        if kb_context:
            context_parts.append(
                "### Detailed Knowledge Base Information:\n"
                + "\n\n---\n\n".join(kb_context)
            )
        if chat_history:
            history_text = "\n".join(f"{h['role']}: {h['content']}" for h in chat_history)
            context_parts.append("### Previous Conversation Context:\n" + history_text)

        context = "\n\n".join(context_parts)
        prompt = (
            f"{context}\n\n"
            f"User Question/Statement: {message}\n\n"
            "Please provide an empathetic, clear, structured, and thoroughly explained response "
            "synthesizing the knowledge base context where applicable."
        )

        response = llm_service.generate(prompt, system=SYSTEM_PROMPT, temperature=0.7)

        pinecone_service.store_chat(session_id, "user", message, query_embedding)
        pinecone_service.store_chat(session_id, "assistant", response, encode_text(response))

        return {"response": response, "session_id": session_id}


chatbot_service = ChatbotService()

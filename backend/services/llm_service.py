import json
import logging
import os

from config import Config

logger = logging.getLogger(__name__)

# Try importing official Groq SDK if installed
try:
    from groq import Groq
    GROQ_SDK_AVAILABLE = True
except ImportError:
    GROQ_SDK_AVAILABLE = False

# Try importing requests; fallback to urllib if not installed
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    import urllib.error
    import urllib.request


class LLMService:
    def __init__(self):
        self._groq_client = None

    def _get_groq_client(self):
        api_key = Config.GROQ_API_KEY.strip() if Config.GROQ_API_KEY else ""
        if GROQ_SDK_AVAILABLE and api_key:
            if self._groq_client is None:
                self._groq_client = Groq(api_key=api_key)
            return self._groq_client
        return None

    def generate(
        self,
        prompt: str,
        system: str = "",
        json_mode: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a text or JSON completion using Groq (default) or fallback to local Ollama.
        """
        provider = Config.LLM_PROVIDER.lower()
        groq_api_key = Config.GROQ_API_KEY.strip() if Config.GROQ_API_KEY else ""

        # Prioritize Groq if provider is groq or GROQ_API_KEY is present
        if provider == "groq" or (groq_api_key and provider != "ollama"):
            if not groq_api_key:
                logger.warning("GROQ_API_KEY is not set in backend/.env. Attempting fallback.")
                return self._handle_missing_groq_key(prompt, system)

            try:
                return self._call_groq(
                    prompt=prompt,
                    system=system,
                    json_mode=json_mode,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                logger.error(f"Groq API error: {e}. Trying fallback...")
                # Attempt Ollama fallback before returning offline message
                ollama_resp = self._call_ollama(prompt, system)
                if ollama_resp:
                    return ollama_resp
                return self._fallback_response(prompt, error=str(e))

        # Default Ollama path if explicitly configured
        ollama_resp = self._call_ollama(prompt, system)
        if ollama_resp:
            return ollama_resp

        return self._fallback_response(prompt)

    def _call_groq(
        self,
        prompt: str,
        system: str,
        json_mode: bool,
        temperature: float,
        max_tokens: int,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # 1. Use Groq SDK if available
        client = self._get_groq_client()
        if client:
            kwargs = {
                "model": Config.GROQ_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            completion = client.chat.completions.create(**kwargs)
            return completion.choices[0].message.content or ""

        # 2. HTTP call to Groq OpenAI-compatible API endpoint
        headers = {
            "Authorization": f"Bearer {Config.GROQ_API_KEY.strip()}",
            "Content-Type": "application/json",
            "User-Agent": "WellSync/1.0",
        }
        payload = {
            "model": Config.GROQ_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        if REQUESTS_AVAILABLE:
            response = requests.post(
                Config.GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
        else:
            req = urllib.request.Request(
                Config.GROQ_API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))

        choices = data.get("choices", [])
        if choices and "message" in choices[0]:
            return choices[0]["message"].get("content", "")
        return ""

    def _call_ollama(self, prompt: str, system: str = "") -> str | None:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        payload = {
            "model": Config.LLM_MODEL,
            "prompt": full_prompt,
            "stream": False,
        }

        try:
            if REQUESTS_AVAILABLE:
                response = requests.post(
                    Config.LLM_API_URL,
                    json=payload,
                    timeout=30,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", data.get("text", ""))
            else:
                req = urllib.request.Request(
                    Config.LLM_API_URL,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("response", data.get("text", ""))
        except Exception:
            pass
        return None

    def _handle_missing_groq_key(self, prompt: str, system: str) -> str:
        # Check if Ollama is available
        ollama_resp = self._call_ollama(prompt, system)
        if ollama_resp:
            return ollama_resp

        return (
            "Groq API Key Required: To enable the high-speed Groq LLM, please set "
            "`GROQ_API_KEY=your_key_here` in `backend/.env`.\n\n"
            "You can obtain a free Groq API key instantly at https://console.groq.com/keys.\n\n"
            "In the meantime, remember that taking a slow deep breath, grounding yourself in the present, "
            "and reaching out to someone you trust can help restore a sense of calm."
        )

    def _fallback_response(self, prompt: str, error: str = "") -> str:
        return (
            "I'm here to support your mental wellness journey. "
            "While the AI model is currently taking a moment to reconnect, remember that "
            "taking deep breaths (like the 4-7-8 technique or physiological sigh), "
            "staying grounded, and seeking professional guidance for challenging feelings "
            "are all powerful practices.\n\n"
            "Please check your API connection or try again shortly."
        )


llm_service = LLMService()

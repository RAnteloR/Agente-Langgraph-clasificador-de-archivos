"""Fábrica del objeto de conexión con el LLM: cambiar de modelo es cambiar parámetros."""
import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()

PROVIDERS = ("ollama", "gemini")
DEFAULT_MODELS = {"ollama": "llama3.1:8b-instruct-q4_K_M", "gemini": "gemini-2.5-flash"}


def gemini_keys() -> list[str]:
    """Claves Gemini configuradas (GOOGLE_API_KEYS separadas por comas)."""
    raw = os.getenv("GOOGLE_API_KEYS") or os.getenv("GOOGLE_API_KEY", "")
    return [k.strip() for k in raw.split(",") if k.strip()]


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0,
    key_index: int = 0,
) -> BaseChatModel:
    """Devuelve un chat model de LangChain.

    provider: "ollama" | "gemini" (por defecto LLM_PROVIDER del .env)
    model: nombre del modelo (por defecto LLM_MODEL si coincide el proveedor del .env,
           si no, el modelo por defecto del proveedor)
    key_index: qué API key de Gemini usar; permite rotar cuando se agota la cuota.
    """
    env_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    provider = (provider or env_provider).lower()
    if provider not in PROVIDERS:
        raise ValueError(f"Proveedor '{provider}' no soportado. Usa uno de {PROVIDERS}.")
    if model is None:
        model = os.getenv("LLM_MODEL") if provider == env_provider else None
        model = model or DEFAULT_MODELS[provider]

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    from langchain_google_genai import ChatGoogleGenerativeAI

    keys = gemini_keys()
    if not keys:
        raise RuntimeError("Falta GOOGLE_API_KEYS en el .env para usar Gemini.")
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=keys[key_index % len(keys)],
    )

"""Fábrica del LLM: el modelo se elige con un solo texto "proveedor/modelo".

Ejemplos: ollama/llama3.1:8b-instruct-q4_K_M   gemini/gemini-2.5-flash
"""
import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()


def gemini_keys() -> list[str]:
    """Claves Gemini configuradas (GOOGLE_API_KEYS separadas por comas)."""
    return [k.strip() for k in os.getenv("GOOGLE_API_KEYS", "").split(",") if k.strip()]


def get_llm(modelo: str | None = None, temperature: float = 0, key_index: int = 0) -> BaseChatModel:
    """modelo: "proveedor/modelo" (por defecto la variable MODELO del .env).
    key_index: qué API key de Gemini usar, para cambiar de cuenta si se agota la cuota."""
    modelo = modelo or os.getenv("MODELO", "ollama/llama3.1:8b-instruct-q4_K_M")
    proveedor, _, nombre = modelo.partition("/")
    proveedor = proveedor.lower()
    if not nombre:
        raise ValueError(f"Formato de modelo no válido: '{modelo}'. Usa proveedor/modelo.")

    if proveedor == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=nombre,
            temperature=temperature,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    if proveedor == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        keys = gemini_keys()
        if not keys:
            raise RuntimeError("Falta GOOGLE_API_KEYS en el .env para usar Gemini.")
        return ChatGoogleGenerativeAI(
            model=nombre, temperature=temperature, google_api_key=keys[key_index % len(keys)]
        )
    raise ValueError(f"Proveedor '{proveedor}' no soportado. Usa ollama o gemini.")

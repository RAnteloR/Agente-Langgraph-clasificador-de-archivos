"""Cliente CLI: agente ReAct (LangGraph) que usa las tools del servidor MCP.

Uso: uv run python main.py [--modelo proveedor/modelo] [--key N]
El servidor MCP debe estar arrancado: uv run python server.py
"""
import argparse
import asyncio
import os

from dotenv import load_dotenv
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from llm import get_llm

load_dotenv()
MCP_URL = f"http://{os.getenv('MCP_HOST', '127.0.0.1')}:{os.getenv('MCP_PORT', '8000')}/mcp"

SYSTEM_PROMPT = """Eres un asistente que gestiona archivos de texto con herramientas MCP. Responde en español.
Flujo: los archivos se suben o guardan en 'recepcion' (pendientes) y luego se clasifican por tema.
- Ver qué hay para subir: listar_directorio_base.
- Subir un archivo existente del directorio base: subir_archivo. NO lo clasifiques salvo que te lo pidan.
- Guardar un texto que escribe el usuario: guardar_texto. NO lo clasifiques salvo que te lo pidan.
- Clasificar: listar_pendientes y listar_temas; para CADA pendiente usa leer_archivo, elige UN tema de
  listar_temas según su contenido ('otros' si no encaja) y llama a mover_a_tema.
- Ver los archivos ya clasificados de un tema: listar_por_tema.
No inventes nombres de archivo ni temas."""


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", help="p. ej. ollama/llama3.1:8b-instruct-q4_K_M o gemini/gemini-2.5-flash")
    ap.add_argument("--key", type=int, default=0, help="índice de la API key de Gemini")
    a = ap.parse_args()
    llm = get_llm(a.modelo, key_index=a.key)

    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            print("Tools disponibles:", ", ".join(t.name for t in tools))
            app = create_react_agent(llm, tools, checkpointer=MemorySaver(), prompt=SYSTEM_PROMPT)
            config = {"configurable": {"thread_id": "clasificador_1"}}

            while True:
                pregunta = await asyncio.to_thread(input, "Pregunta>>> ")
                if pregunta.lower() in ("salir", "exit", "quit"):
                    print("Chat terminado")
                    break
                try:
                    async for s in app.astream({"messages": [("user", pregunta)]}, config, stream_mode="values"):
                        msg = s["messages"][-1]
                        for tc in getattr(msg, "tool_calls", None) or []:
                            print(f"   [MCP: {tc['name']}({tc['args']})]")
                except Exception as e:
                    print(f"\nERROR del modelo: {str(e)[:200]}\n(Si es una cuota agotada, prueba otra clave con --key N u otro modelo.)\n")
                    continue
                print(f"\nRESPUESTA FINAL:\n{msg.text}\n")


if __name__ == "__main__":
    asyncio.run(main())

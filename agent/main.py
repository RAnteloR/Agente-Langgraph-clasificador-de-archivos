"""Cliente CLI: agente ReAct (LangGraph) que usa las tools del servidor MCP.

Uso: uv run python agent/main.py [--provider ollama|gemini] [--model NOMBRE] [--key N]
El servidor MCP debe estar arrancado: uv run python mcp_server/server.py
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
- Subir un archivo: usa subir_archivo con el nombre (listar_directorio_base muestra los disponibles).
- Guardar un texto del usuario como archivo: usa guardar_texto.
- Clasificar: usa listar_temas y listar_pendientes; para CADA archivo pendiente usa leer_archivo,
  elige según su contenido UN tema de listar_temas (si no encaja, 'otros') y llama a mover_a_tema.
- Listar los archivos de un tema: usa listar_por_tema.
No inventes nombres de archivo ni temas."""


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider")
    ap.add_argument("--model")
    ap.add_argument("--key", type=int, default=0, help="índice de la API key de Gemini")
    a = ap.parse_args()
    llm = get_llm(a.provider, a.model, key_index=a.key)

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
                async for s in app.astream({"messages": [("user", pregunta)]}, config, stream_mode="values"):
                    msg = s["messages"][-1]
                    for tc in getattr(msg, "tool_calls", None) or []:
                        print(f"   [MCP: {tc['name']}({tc['args']})]")
                print(f"\nRESPUESTA FINAL:\n{msg.content}\n")


if __name__ == "__main__":
    asyncio.run(main())

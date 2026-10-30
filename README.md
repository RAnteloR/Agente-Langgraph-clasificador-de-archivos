# Clasificador de archivos con LangGraph + MCP

Agente (LangGraph, ReAct) que gestiona archivos de texto usando las tools de un servidor MCP por HTTP.
El LLM se elige con una sola variable: `MODELO=ollama/...` o `MODELO=gemini/...`.

## Estructura

```
server.py              Servidor MCP (FastMCP, HTTP) con todas las tools
llm.py                 get_llm("proveedor/modelo"): Ollama o Gemini
main.py                Agente ReAct + chat por terminal
data/descargas/        Directorio base con archivos de prueba
data/recepcion/        Archivos subidos; los temas son subcarpetas (recepcion/<tema>/)
docker-compose.yml     Ollama en Docker
```

## Instalación

```
uv venv && uv pip install -r requirements.txt     # o: python -m venv .venv && pip install -r requirements.txt
cp .env.example .env                              # y edita MODELO y GOOGLE_API_KEYS
```

- **Gemini:** pon tus claves en `GOOGLE_API_KEYS` (separadas por comas) y `MODELO=gemini/gemini-2.5-flash`.
- **Ollama:** `docker compose up -d` y `docker compose exec ollama ollama pull llama3.1:8b-instruct-q4_K_M`.

## Ejecución

```
.venv/bin/python server.py      # terminal 1 (http://127.0.0.1:8000/mcp)
.venv/bin/python main.py             # terminal 2
.venv/bin/python main.py --modelo gemini/gemini-2.5-flash --key 1   # otro modelo / otra API key
```

## Tools MCP

| Tool | Función |
|---|---|
| `listar_directorio_base` | Archivos disponibles en el directorio base |
| `subir_archivo` | Copia un archivo del directorio base a `recepcion` |
| `guardar_texto` | Guarda un texto del teclado como `.txt` en `recepcion` |
| `listar_pendientes` | Archivos de `recepcion` sin clasificar |
| `leer_archivo` | Contenido de un archivo pendiente |
| `listar_temas` | Temas prefijados (`TEMAS` en `.env`) |
| `mover_a_tema` | Mueve el archivo a `recepcion/<tema>/` (la crea si no existe) |
| `listar_por_tema` | Archivos de un tema |

## Archivos de prueba (`data/descargas`)

`partido.txt` (gol penalti), `receta.txt` (receta paella), `codigo.txt` (python linux),
`bolsa.txt` (bolsa inversión), `salud.txt` (dolor cabeza), `astronomia.txt` (mapa estelar → "otros").

## Guion de pruebas para las capturas

1. `¿Qué archivos hay en el directorio base?`
2. `Sube partido.txt, receta.txt y astronomia.txt`
3. `Guarda este texto: python y linux`
4. `Clasifica los archivos pendientes`
5. `Lista los archivos de deportes`
6. `Lista los archivos de cocina`

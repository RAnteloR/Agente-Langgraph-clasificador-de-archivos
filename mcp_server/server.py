"""Servidor MCP (HTTP) con las tools del clasificador de archivos."""
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


def _dir(var: str, default: str) -> Path:
    p = Path(os.getenv(var, default))
    return p if p.is_absolute() else ROOT / p


BASE_DIR = _dir("BASE_DIR", "data/descargas")
RECEPCION_DIR = _dir("RECEPCION_DIR", "data/recepcion")
TEMAS = [
    t.strip().lower()
    for t in os.getenv("TEMAS", "tecnología,deportes,cocina,finanzas,salud,otros").split(",")
    if t.strip()
]

mcp = FastMCP(
    "clasificador-archivos",
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "8000")),
)


def _safe(root: Path, nombre: str) -> Path:
    """Resuelve `nombre` dentro de `root` evitando salir de él (path traversal)."""
    if not nombre or Path(nombre).name != nombre:
        raise ValueError(f"Nombre de archivo no válido: {nombre!r}")
    return root / nombre


def _unique(dest: Path) -> Path:
    """Evita sobrescribir: añade _1, _2... si el destino ya existe."""
    if not dest.exists():
        return dest
    i = 1
    while (cand := dest.with_name(f"{dest.stem}_{i}{dest.suffix}")).exists():
        i += 1
    return cand


@mcp.tool()
def listar_temas() -> list[str]:
    """Devuelve la lista de temas prefijados en los que se puede clasificar."""
    return TEMAS


@mcp.tool()
def listar_directorio_base() -> list[str]:
    """Lista los archivos disponibles en el directorio base (p. ej. descargas)."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(p.name for p in BASE_DIR.iterdir() if p.is_file() and not p.name.startswith("."))


@mcp.tool()
def subir_archivo(nombre: str) -> str:
    """Copia un archivo del directorio base a la carpeta 'recepcion' (simula un upload)."""
    origen = _safe(BASE_DIR, nombre)
    if not origen.is_file():
        return f"ERROR: '{nombre}' no existe en el directorio base."
    RECEPCION_DIR.mkdir(parents=True, exist_ok=True)
    destino = _unique(RECEPCION_DIR / origen.name)
    shutil.copy2(origen, destino)
    return f"OK: '{destino.name}' copiado a recepcion."


@mcp.tool()
def guardar_texto(nombre: str, contenido: str) -> str:
    """Guarda un texto como archivo .txt en la carpeta 'recepcion'."""
    if not nombre.endswith(".txt"):
        nombre += ".txt"
    destino = _unique(_safe(RECEPCION_DIR, nombre))
    RECEPCION_DIR.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")
    return f"OK: texto guardado como '{destino.name}' en recepcion."


@mcp.tool()
def listar_pendientes() -> list[str]:
    """Lista los archivos de 'recepcion' pendientes de clasificar."""
    RECEPCION_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(p.name for p in RECEPCION_DIR.iterdir() if p.is_file() and not p.name.startswith("."))


@mcp.tool()
def leer_archivo(nombre: str) -> str:
    """Devuelve el contenido de un archivo pendiente en 'recepcion'."""
    ruta = _safe(RECEPCION_DIR, nombre)
    if not ruta.is_file():
        return f"ERROR: '{nombre}' no existe en recepcion."
    return ruta.read_text(encoding="utf-8", errors="replace")


@mcp.tool()
def mover_a_tema(nombre: str, tema: str) -> str:
    """Mueve un archivo pendiente de 'recepcion' a la subcarpeta del tema (se crea si no existe)."""
    tema = tema.strip().lower()
    if tema not in TEMAS:
        return f"ERROR: tema '{tema}' no válido. Temas: {', '.join(TEMAS)}."
    origen = _safe(RECEPCION_DIR, nombre)
    if not origen.is_file():
        return f"ERROR: '{nombre}' no existe en recepcion."
    carpeta = RECEPCION_DIR / tema
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = _unique(carpeta / origen.name)
    shutil.move(str(origen), destino)
    return f"OK: '{origen.name}' movido a '{tema}'."


@mcp.tool()
def listar_por_tema(tema: str) -> list[str]:
    """Lista los archivos clasificados bajo un tema."""
    tema = tema.strip().lower()
    carpeta = RECEPCION_DIR / tema
    if tema not in TEMAS or not carpeta.is_dir():
        return []
    return sorted(p.name for p in carpeta.iterdir() if p.is_file() and not p.name.startswith("."))


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

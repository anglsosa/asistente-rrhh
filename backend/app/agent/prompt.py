from pathlib import Path

CARPETA_PROMPTS = Path(__file__).parent / "prompts"


def cargar_prompt(version: str) -> str:
    """
    Lee el system prompt versionado: prompts/sistema_<version>.md
    """
    ruta = CARPETA_PROMPTS / f"sistema_{version}.md"
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el prompt {ruta.name}: revisa APP_PROMPT_VERSION")
    return ruta.read_text(encoding="utf-8")
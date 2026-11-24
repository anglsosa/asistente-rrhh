import re
from dataclasses import dataclass
from pathlib import Path

PATRON_ARTICULO = re.compile(r"^###\s+(Artículo\s+\d+(?:-[A-Z]|\s+Bis)?)\.\s*(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class Fragmento:
    """
    Un artículo completo que esla unidad que se indexa, se busca y se cita
    """

    id: str
    documento: str
    articulo: str
    titulo: str
    texto: str


def partir_por_articulo(contenido: str, documento: str) -> list[Fragmento]:
    """
    Un fragmento por cada ### Artículo N. Título,
    sin artículos, el documento completo
    """
    encabezados = list(PATRON_ARTICULO.finditer(contenido))
    if not encabezados:
        return [
            Fragmento(
                id=f"{documento}#completo",
                documento=documento,
                articulo="Documento completo",
                titulo=documento,
                texto=contenido.strip(),
            )
        ]

    fragmentos: list[Fragmento] = []
    for i, encabezado in enumerate(encabezados):
        fin = encabezados[i + 1].start() if i + 1 < len(encabezados) else len(contenido)
        cuerpo = contenido[encabezado.end() : fin].strip()
        articulo, titulo = encabezado.group(1), encabezado.group(2).strip()
        numero = articulo.removeprefix("Artículo").strip().replace(" ", "-").lower()
        fragmentos.append(
            Fragmento(
                id=f"{documento}#art-{numero}",
                documento=documento,
                articulo=articulo,
                titulo=titulo,
                texto=f"{articulo}. {titulo}\n{cuerpo}",
            )
        )
    return fragmentos


def cargar_documentos(directorio: Path) -> list[Fragmento]:
    """
    Lee todos los .md del directorio y los parte por artículo
    """
    fragmentos: list[Fragmento] = []
    for archivo in sorted(directorio.glob("*.md")):
        contenido = archivo.read_text(encoding="utf-8")
        fragmentos.extend(partir_por_articulo(contenido, archivo.stem))
    return fragmentos

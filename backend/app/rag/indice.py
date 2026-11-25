from pathlib import Path

import chromadb

from app.rag.busqueda import fusionar_rrf
from app.rag.fragmentos import Fragmento, cargar_documentos
from app.schemas.politicas import ResultadoBusqueda


class IndicePoliticas:
    def __init__(self, directorio: Path) -> None:
        cliente = chromadb.PersistentClient(path=str(directorio))
        self._coleccion = cliente.get_or_create_collection("politicas")
        self._fragmentos = dict[str, Fragmento] = {}

    def indexar(self, fragmentos: list[Fragmento]) -> int:
        """
        Guarda los fragmentos, actualiza si ya existian y borra si ya no existen
        """

        if not fragmentos:
            raise ValueError("No hay documentos para indexar")

        self._fragmentos = {f.id: f for f in fragmentos}

        self._coleccion.upsert(
            ids=list(self._fragmentos),
            documents=[f.text for f in fragmentos],
            metadatas=[{"documento": f.documento, "articulo": f.articulo} for f in fragmentos],
        )

        sobrantes = set(self._coleccion.get()["ids"]) - self._fragmentos.keys()
        if sobrantes:
            self._coleccion.delete(ids=list(sobrantes))

        return len(fragmentos)

    def buscar(self, pregunta: str, k: int = 3) -> list[ResultadoBusqueda]:
        """
        Los k artículos más relevantes para la pregunta
        """
        candidatos = max(k * 3, 10)
        por_significado = self._buscar_por_significado(pregunta, candidatos)
        fusion = fusionar_rrf([por_significado])[:k]
        return [self._resultado(doc_id, puntaje) for doc_id, puntaje in fusion]

    def _buscar_por_significado(self, pregunta: str, n: int) -> list[str]:
        n = min(n, self._coleccion.count())
        respuesta = self._coleccion.query(query_texts=[pregunta], n_results=n)
        return [doc_id for doc_id in respuesta["ids"][0] if doc_id in self._fragmentos]

    def _resultado(self, doc_id: str, puntaje: float) -> ResultadoBusqueda:
        f = self._fragmentos[doc_id]
        return ResultadoBusqueda(
            id=f.id,
            documento=f.documento,
            articulo=f.articulo,
            titulo=f.titulo,
            texto=f.texto,
            puntaje=round(puntaje, 4),
        )


def construir_indice(data_dir: Path, chroma_dir: Path) -> IndicePoliticas:
    """
    Carga, parte e indexa los documentos. Es lento y síncrono: se llama en un hilo aparte
    """
    indice = IndicePoliticas(chroma_dir)
    indice.indexar(cargar_documentos(data_dir))
    return indice

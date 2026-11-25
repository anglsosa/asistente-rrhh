# ADR 0003 RAG por artículo con búsqueda híbrida

**Contexto:** las respuestas tienen que citar artículos exactos de documentos en español y no quería levantar servidores extra

**Opciones**

- Partir los documentos en pedazos de tamaño fijo o partirlos por artículo
- Búsqueda solo vectorial o híbrida con BM25
- Chroma local o pgvector

**Decisión:** un fragmento por artículo, Chroma local con embeddings locales más BM25, y las dos listas se juntan con Reciprocal Rank Fusion (k = 60)

**Consecuencias:** cada fragmento es una regla completa que se puede citar, cuando probé "prima vacacional" la búsqueda vectorial no encontró el artículo y BM25 sí, eso confirmó que valía la pena la búsqueda híbrida, lo que queda débil es la calidad semántica en español y lo siguiente sería usar embeddings multilingües

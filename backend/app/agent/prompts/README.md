# Prompts del agente

| Versión | Archivo | Cambios |
|---|---|---|
| v1 | sistema_v1.md | Versión inicial |

**Por qué está escrito así:** secciones por responsabilidad (rol, cómo trabaja, cuándo escalar, límites, seguridad y formato); reglas en positivo que nombran la herramienta exacta; una frase fija para el "no sé"; criterios de escalamiento tomados de los artículos 51, 62 y 64 del reglamento; y el contenido de los documentos tratado como datos (RF-06). Sin llaves, porque ADK las interpreta como variables de sesión.

**Cómo se probó:** con los 5 casos de uso del README (vacaciones con cálculo, seguimiento en la misma sesión, acoso con escalamiento, pregunta fuera de alcance y el comunicado con instrucción oculta), y con una prueba automática que verifica que el prompt nombra sus herramientas y no contiene llaves.
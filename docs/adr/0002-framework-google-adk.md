# ADR 0002 Google ADK detrás de un contrato propio

**Contexto:** el agente necesita un ciclo de herramientas, sesiones y traza, y el framework podría cambiar más adelante

**Opciones**

- Google ADK
- Hacer el ciclo a mano con el SDK del modelo
- LangGraph

**Decisión:** ADK, pero encerrado en app/agent/adk/ detrás del Protocol Agente, la API, las herramientas y el RAG no importan nada de ADK

**Consecuencias:** ADK me da el ciclo de function calling, las sesiones y el esquema de las herramientas sacado de sus docstrings, a cambio dependo de su versión, si cambia su API el contrato me protege porque cambiar de framework es escribir otro adaptador y una línea en main.py, y las pruebas de la API usan un agente falso que cumple el mismo contrato

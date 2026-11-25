# Agente asistente_politicas

**Propósito y alcance:** responde dudas de políticas de RRHH citando el reglamento interior y la LFT, calcula vacaciones y escala a RRHH, no da asesoría legal, no aprueba ni niega solicitudes y no consulta datos personales

**Modelo y parámetros:** gemini-3.5-flash configurable con APP_GEMINI_MODELO, temperatura 0.2 para que las respuestas sean consistentes y fieles al documento, nivel de razonamiento LOW para bajar la latencia, máximo 1024 tokens porque las respuestas son de 2 a 5 oraciones, y timeout configurable con APP_TIMEOUT_AGENTE_SEG (45 segundos por defecto)

**Prompt:** backend/app/agent/prompts/sistema_v1.md, la versión se elige con APP_PROMPT_VERSION y en la misma carpeta hay un README con por qué está escrito así y cómo se probó

**Tools**

| Nombre | Para qué | Entrada | Salida | Errores |
|---|---|---|---|---|
| buscar_politicas | Encontrar los artículos que responden la duda | pregunta | Artículos con documento, número, título y texto | Si no hay nada regresa sin resultados |
| calcular_vacaciones | Días de vacaciones y prima vacacional | anios_antiguedad y salario_diario opcional | Días, porcentaje, monto de la prima y fundamento | Antigüedad negativa regresa status error |
| escalar_a_rrhh | Crear un ticket para RRHH | tema, resumen y prioridad, el empleado sale de la sesión | Folio RRHH-AAAA-NNNNN | Datos inválidos regresan status error |

**Datos y memoria:** usa data/politicas (reglamento ficticio, extractos literales de la LFT y un comunicado de prueba), se indexa por artículo en Chroma y BM25 al arrancar, y entre turnos guarda el historial y el empleado_id en la sesión de ADK, que vive en memoria

**Flujo**

1. Recibe el mensaje en POST /api/v1/chat
2. Busca en las políticas
3. Si hay cifras usa calcular_vacaciones
4. Responde citando, o escala si no encontró nada o el tema es delicado
5. Regresa la respuesta, las fuentes, la traza, el folio si hubo y cuánto tardó

**Límites y salvaguardas:** si la pregunta no es de RRHH dice que solo atiende eso, contra prompt injection el prompt trata los documentos como datos, cada resultado de búsqueda lo recuerda y el empleado_id no lo controla el modelo, si una herramienta falla regresa status error para que el agente lo explique o escale, y si el modelo falla o tarda la API responde 429, 502 o 504

**Ejemplos**

1. "Tengo 3 años, ¿cuántos días de vacaciones me tocan?" responde 16 días (Reglamento interior Art. 21 y LFT Art. 76)
2. "Mi jefe me acosa" cita el Art. 51 y escala con folio de prioridad alta
3. "¿Cuál es la capital de Francia?" responde que solo atiende dudas de RRHH

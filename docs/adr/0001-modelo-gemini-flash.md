# ADR 0001 Modelo Gemini 3.5 Flash

**Contexto:** quien evalúe el proyecto lo va a correr con su propia API key, las preguntas son cortas y muy frecuentes, y necesito que el modelo use bien las herramientas y responda rápido

**Opciones**

- Gemini Flash, tiene capa gratuita en AI Studio
- Claude, muy buena calidad pero es de pago
- Un modelo local con Ollama, es gratis pero hay que instalarlo y descargar varios GB

**Decisión:** gemini-3.5-flash con temperatura 0.2 y nivel de razonamiento LOW, se puede cambiar con APP_GEMINI_MODELO sin tocar código

**Consecuencias:** gano costo cero para quien lo pruebe y buen function calling, a cambio no controlo la velocidad ni los límites de la capa gratuita, en pruebas una respuesta pasó de 45 segundos y por eso bajé el razonamiento a LOW y dejé el timeout configurable, si sale un 429 o un 504 la API responde con un mensaje claro en lugar de tronar

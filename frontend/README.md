# Frontend

Interfaz de chat para el asistente de políticas de RRHH, hecha con Vite, React, TypeScript y Tailwind

```bash
npm install
npm run dev
```

Queda en http://localhost:5173 y manda las peticiones de /api al backend en el puerto 8000 con el proxy de Vite, por eso no hace falta abrir CORS en FastAPI

- `src/api.ts` tiene los tipos de la respuesta y la llamada a POST /api/v1/chat
- `src/App.tsx` tiene el chat, guarda el sesion_id para que el agente recuerde la conversación y muestra fuentes, folio y traza
- Las respuestas se muestran con formato usando react-markdown, que no ejecuta HTML del modelo

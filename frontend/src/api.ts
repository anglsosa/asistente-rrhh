export type Fuente = { documento: string; articulo: string; titulo: string };

export type PasoTraza = {
	herramienta: string;
	argumentos: Record<string, unknown>;
	resumen: string | null;
};

export type ChatRespuesta = {
	sesion_id: string;
	respuesta: string;
	fuentes: Fuente[];
	traza: PasoTraza[];
	folio_escalamiento: string | null;
	duracion_ms: number;
};

export async function enviarMensaje(
	mensaje: string,
	empleadoId: string,
	sesionId: string | null,
): Promise<ChatRespuesta> {
	const response = await fetch("/api/v1/chat", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({
			mensaje,
			empleado_id: empleadoId,
			sesion_id: sesionId,
		}),
	});
	if (!response.ok) {
		// 429, 502 y 504 traen un detail en texto, el 422 trae una lista
		const error = await response.json().catch(() => null);
		throw new Error(
			typeof error?.detail === "string"
				? error.detail
				: `Error ${response.status}`,
		);
	}
	return response.json();
}

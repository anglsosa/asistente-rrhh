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

export type EventoStream =
	| { tipo: "texto"; datos: { texto: string } }
	| { tipo: "paso"; datos: PasoTraza }
	| { tipo: "fin"; datos: ChatRespuesta }
	| { tipo: "error"; datos: { status: number; detail: string } };

// Lee el SSE de /api/v1/chat/stream con fetch porque EventSource solo permite GET
export async function* enviarMensajeStream(
	mensaje: string,
	empleadoId: string,
	sesionId: string | null,
): AsyncGenerator<EventoStream> {
	const response = await fetch("/api/v1/chat/stream", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({
			mensaje,
			empleado_id: empleadoId,
			sesion_id: sesionId,
		}),
	});
	if (!response.ok || !response.body) {
		const error = await response.json().catch(() => null);
		throw new Error(
			typeof error?.detail === "string"
				? error.detail
				: `Error ${response.status}`,
		);
	}
	const lector = response.body.pipeThrough(new TextDecoderStream()).getReader();
	let pendiente = "";
	while (true) {
		const { value, done } = await lector.read();
		if (done) break;
		pendiente += value;
		// Cada evento SSE termina con una línea en blanco, lo incompleto espera al siguiente pedazo
		const bloques = pendiente.split("\n\n");
		pendiente = bloques.pop() ?? "";
		for (const bloque of bloques) {
			const evento = leerEvento(bloque);
			if (evento) yield evento;
		}
	}
}

function leerEvento(bloque: string): EventoStream | null {
	let tipo = "";
	const datos: string[] = [];
	for (const linea of bloque.split("\n")) {
		if (linea.startsWith("event:")) tipo = linea.slice(6).trim();
		else if (linea.startsWith("data:")) datos.push(linea.slice(5).trimStart());
	}
	if (!tipo || datos.length === 0) return null;
	return { tipo, datos: JSON.parse(datos.join("\n")) } as EventoStream;
}

import { useEffect, useRef, useState } from "react";
import { enviarMensajeStream, type ChatRespuesta } from "./api";
import Markdown from "react-markdown";

type Mensaje = { autor: "empleado" | "asistente"; texto: string; detalle?: ChatRespuesta };

const EJEMPLOS = [
  "Tengo 3 años en la empresa, ¿cuántos días de vacaciones me tocan?",
  "¿Cuántos días de aguinaldo me dan y cuándo?",
  "Mi jefe me hace comentarios ofensivos todos los días",
];

export default function App() {
  const [empleadoId, setEmpleadoId] = useState("EMP-0042");
  const [sesionId, setSesionId] = useState<string | null>(null);
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [texto, setTexto] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pasoActual, setPasoActual] = useState<string | null>(null);
  const finRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, cargando]);

  function nuevaConversacion() {
    setSesionId(null);
    setMensajes([]);
    setError(null);
  }

  async function enviar(contenido: string) {
    const limpio = contenido.trim();
    if (!limpio || cargando) return;
    // La burbuja del asistente empieza vacía y se va llenando con cada pedazo del stream
    setMensajes((previos) => [
      ...previos,
      { autor: "empleado", texto: limpio },
      { autor: "asistente", texto: "" },
    ]);
    setTexto("");
    setError(null);
    setCargando(true);
    try {
      for await (const evento of enviarMensajeStream(limpio, empleadoId, sesionId)) {
        if (evento.tipo === "texto") {
          actualizarUltimo((m) => ({ ...m, texto: m.texto + evento.datos.texto }));
        } else if (evento.tipo === "paso") {
          setPasoActual(evento.datos.herramienta);
        } else if (evento.tipo === "fin") {
          setSesionId(evento.datos.sesion_id);
          actualizarUltimo(() => ({
            autor: "asistente",
            texto: evento.datos.respuesta,
            detalle: evento.datos,
          }));
        } else {
          throw new Error(evento.datos.detail);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Algo salió mal, intenta de nuevo");
      setMensajes((previos) => (previos.at(-1)?.texto ? previos : previos.slice(0, -1)));
    } finally {
      setCargando(false);
      setPasoActual(null);
    }
  }

  function actualizarUltimo(cambio: (ultimo: Mensaje) => Mensaje) {
    setMensajes((previos) => [...previos.slice(0, -1), cambio(previos[previos.length - 1])]);
  }

  return (
    <div className="flex h-dvh flex-col bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-2xl items-center justify-between gap-3 px-4 py-3">
          <div>
            <h1 className="font-semibold">Asistente de políticas de RRHH</h1>
            <p className="text-xs text-slate-500">Responde citando el reglamento y la LFT</p>
          </div>
          <div className="flex items-center gap-2">
            <input
              value={empleadoId}
              onChange={(e) => {
                setEmpleadoId(e.target.value.toUpperCase());
                nuevaConversacion();
              }}
              aria-label="Número de empleado"
              className="w-28 rounded-lg border border-slate-300 px-2 py-1 text-sm"
            />
            <button
              type="button"
              onClick={nuevaConversacion}
              className="rounded-lg px-2 py-1 text-sm text-slate-600 hover:bg-slate-100"
            >
              Nueva
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-2xl flex-col gap-4 px-4 py-6">
          {mensajes.length === 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-sm text-slate-500">Prueba con alguna de estas preguntas</p>
              {EJEMPLOS.map((ejemplo) => (
                <button
                  key={ejemplo}
                  type="button"
                  onClick={() => void enviar(ejemplo)}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm hover:border-slate-400"
                >
                  {ejemplo}
                </button>
              ))}
            </div>
          )}

          {mensajes.map((m, i) =>
            !m.texto ? null : m.autor === "empleado" ? (
              <p
                key={i}
                className="max-w-[85%] self-end whitespace-pre-wrap rounded-2xl rounded-br-sm bg-slate-900 px-4 py-2 text-sm text-white"
              >
                {m.texto}
              </p>
            ) : (
              <div
                key={i}
                className="max-w-[85%] self-start rounded-2xl rounded-bl-sm border border-slate-200 bg-white px-4 py-3 text-sm"
              >
                <div className="prose prose-sm prose-slate max-w-none">
  					<Markdown>{m.texto}</Markdown>
				</div>
                {m.detalle && <Detalle detalle={m.detalle} />}
              </div>
            ),
          )}

          {cargando && (
            <p className="text-sm text-slate-400">
              {pasoActual ? `Usando ${pasoActual}…` : "Pensando…"}
            </p>
          )}
          {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div ref={finRef} />
        </div>
      </main>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void enviar(texto);
        }}
        className="border-t border-slate-200 bg-white"
      >
        <div className="mx-auto flex max-w-2xl gap-2 px-4 py-3">
          <input
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Escribe tu duda"
            maxLength={2000}
            className="flex-1 rounded-xl border border-slate-300 px-4 py-2 text-sm outline-none focus:border-slate-500"
          />
          <button
            type="submit"
            disabled={cargando || !texto.trim()}
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
          >
            Enviar
          </button>
        </div>
      </form>
    </div>
  );
}

function Detalle({ detalle }: { detalle: ChatRespuesta }) {
  return (
    <div className="mt-3 flex flex-col gap-2 border-t border-slate-100 pt-3 text-xs text-slate-500">
      {detalle.folio_escalamiento && (
        <p className="w-fit rounded-full bg-amber-100 px-2 py-0.5 font-medium text-amber-800">
          Folio {detalle.folio_escalamiento}
        </p>
      )}
      {detalle.fuentes.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {detalle.fuentes.map((f) => (
            <span
              key={`${f.documento}-${f.articulo}`}
              title={f.titulo}
              className="rounded-full bg-slate-100 px-2 py-0.5"
            >
              {f.documento} {f.articulo}
            </span>
          ))}
        </div>
      )}
      <details>
        <summary className="cursor-pointer">
          Traza con {detalle.traza.length} pasos en {detalle.duracion_ms} ms
        </summary>
        <ol className="mt-2 flex flex-col gap-1">
          {detalle.traza.map((paso, i) => (
            <li key={i} className="rounded bg-slate-50 p-2 font-mono">
              <span className="font-semibold text-slate-700">{paso.herramienta}</span>{" "}
              {JSON.stringify(paso.argumentos)}
              {paso.resumen && <span className="block text-slate-400">{`→ ${paso.resumen}`}</span>}
            </li>
          ))}
        </ol>
      </details>
    </div>
  );
}
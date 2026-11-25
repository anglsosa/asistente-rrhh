// Voz con las APIs del navegador: SpeechRecognition para escuchar y speechSynthesis para hablar,
// no necesita API keys ni backend extra

// TypeScript trae los eventos de reconocimiento pero no la clase, por eso se declaran aquí
type Reconocimiento = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((evento: SpeechRecognitionEvent) => void) | null;
  onerror: ((evento: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
};
type ConstructorReconocimiento = new () => Reconocimiento;

const ventana = window as unknown as {
  SpeechRecognition?: ConstructorReconocimiento;
  webkitSpeechRecognition?: ConstructorReconocimiento;
};
const Reconocedor = ventana.SpeechRecognition ?? ventana.webkitSpeechRecognition;

// Firefox no tiene reconocimiento de voz, en ese caso la interfaz oculta el micrófono
export const hayMicrofono = Reconocedor !== undefined;
export const hayVoz = "speechSynthesis" in window;

/**
 * Escucha en español y va mandando la transcripción en vivo mientras hablas,
 * termina sola después de un silencio o cuando se llama a la función que regresa,
 * y en los dos casos entrega el texto completo en alTerminar
 */
export function escuchar(
  alTexto: (texto: string) => void,
  alTerminar: (texto: string) => void,
  alError: (mensaje: string) => void,
  silencioMs = 1500,
): () => void {
  if (!Reconocedor) {
    alTerminar("");
    return () => {};
  }
  const reconocimiento = new Reconocedor();
  reconocimiento.lang = "es-MX";
  reconocimiento.interimResults = true;
  // continuous evita que Chrome corte en la primera pausa corta, el corte lo decide el temporizador
  reconocimiento.continuous = true;
  let texto = "";
  let temporizador: number | undefined;
  reconocimiento.onresult = (evento) => {
    texto = "";
    for (let i = 0; i < evento.results.length; i++) {
      texto += evento.results[i][0].transcript;
    }
    alTexto(texto);
    // Cada palabra nueva reinicia la cuenta, si te callas silencioMs se detiene
    window.clearTimeout(temporizador);
    temporizador = window.setTimeout(() => reconocimiento.stop(), silencioMs);
  };
  reconocimiento.onerror = (evento) => {
    // no-speech y aborted no son fallas: no dijo nada o se detuvo a propósito
    if (evento.error === "no-speech" || evento.error === "aborted") return;
    alError(MENSAJES_ERROR[evento.error] ?? `No se pudo usar el micrófono (${evento.error})`);
  };
  // onend llega al detenerlo, después del silencio o si el navegador corta por un error
  reconocimiento.onend = () => {
    window.clearTimeout(temporizador);
    alTerminar(texto.trim());
  };
  try {
    reconocimiento.start();
  } catch {
    alError("No se pudo iniciar el micrófono, recarga la página e intenta de nuevo");
    alTerminar("");
  }
  return () => reconocimiento.stop();
}

const MENSAJES_ERROR: Record<string, string> = {
  "not-allowed":
    "El micrófono está bloqueado, permítelo en el candado de la barra de direcciones y en Ajustes del sistema > Privacidad > Micrófono",
  "service-not-allowed":
    "Este navegador no permite el reconocimiento de voz, usa Chrome o Edge",
  "audio-capture": "No se encontró un micrófono conectado",
  network: "El reconocimiento de voz de este navegador no está disponible, usa Chrome o Edge",
};

/**
 * Lee en voz alta la respuesta mientras llega del stream, habla cada oración completa
 * en cuanto se termina de escribir en lugar de esperar toda la respuesta
 */
export class Locutor {
  private pendiente = "";
  private hablado = false;
  private enFuentes = false;

  iniciar() {
    this.callar();
    this.hablado = false;
    this.enFuentes = false;
  }

  agregar(trozo: string) {
    this.pendiente += trozo;
    const completas = this.pendiente.match(/^[\s\S]*[.!?\n](?=\s)/);
    if (completas) {
      this.pendiente = this.pendiente.slice(completas[0].length);
      this.hablar(completas[0]);
    }
  }

  // Si el stream no mandó pedazos se lee la respuesta completa
  terminar(respuestaCompleta: string) {
    const resto = this.hablado ? this.pendiente : respuestaCompleta;
    this.pendiente = "";
    this.hablar(resto);
  }

  // Interrupción: corta lo que está diciendo y lo que faltaba por decir
  callar() {
    this.pendiente = "";
    if (hayVoz) speechSynthesis.cancel();
  }

  private hablar(texto: string) {
    // Las fuentes se ven en pantalla, leerlas en voz alta solo estorba
    if (/^\W*fuentes/i.test(texto.trim())) this.enFuentes = true;
    const limpio = limpiarParaVoz(texto);
    if (!hayVoz || this.enFuentes || !limpio) return;
    const frase = new SpeechSynthesisUtterance(limpio);
    frase.lang = "es-MX";
    const voces = speechSynthesis.getVoices();
    const voz = voces.find((v) => v.lang === "es-MX") ?? voces.find((v) => v.lang.startsWith("es"));
    if (voz) frase.voice = voz;
    speechSynthesis.speak(frase);
    this.hablado = true;
  }
}

// Quita markdown y citas entre paréntesis para que no lea asteriscos ni números de artículo
export function limpiarParaVoz(texto: string): string {
  return texto
    .replace(/\([^)]*Art[^)]*\)/g, "")
    .replace(/[*_#`>]/g, "")
    .replace(/\s+/g, " ")
    .replace(/\s+([.,;!?])/g, "$1")
    .trim();
}

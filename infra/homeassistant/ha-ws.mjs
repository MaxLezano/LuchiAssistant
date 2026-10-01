// Cliente mínimo de la API WebSocket de Home Assistant (Node 22+, sin dependencias).
// Uso: LUCHI_HA_TOKEN=... node ha-ws.mjs '<json de un comando o lista>' | @comandos.json [url]
// Imprime el resultado de cada comando como JSON. El token se lee del entorno, nunca de archivos.
import { readFileSync } from "node:fs";
const arg = process.argv[2] ?? "[]";
const comandos = [].concat(JSON.parse(arg.startsWith("@") ? readFileSync(arg.slice(1), "utf8") : arg));
const url = (process.argv[3] ?? "http://homeassistant.local").replace(/^http/, "ws") + "/api/websocket";
const token = process.env.LUCHI_HA_TOKEN;
if (!token) { console.error("Falta LUCHI_HA_TOKEN"); process.exit(1); }

const ws = new WebSocket(url);
let id = 0;
const pendientes = new Map();
const enviar = (cmd) => new Promise((resolve) => { const n = ++id; pendientes.set(n, resolve); ws.send(JSON.stringify({ id: n, ...cmd })); });

ws.onmessage = async ({ data }) => {
  const msg = JSON.parse(data);
  if (msg.type === "auth_required") ws.send(JSON.stringify({ type: "auth", access_token: token }));
  else if (msg.type === "auth_invalid") { console.error("Token inválido"); process.exit(1); }
  else if (msg.type === "auth_ok") {
    let ok = true;
    for (const cmd of comandos) {
      const r = await enviar(cmd);
      ok &&= r.success;
      console.log(JSON.stringify({ type: cmd.type, success: r.success, result: r.result, error: r.error }));
    }
    ws.close();
    process.exit(ok ? 0 : 1);
  } else if (msg.type === "result") pendientes.get(msg.id)?.(msg);
};
ws.onerror = (e) => { console.error("Error de conexión:", e.message ?? e); process.exit(1); };

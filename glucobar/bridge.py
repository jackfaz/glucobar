"""Ponte locale (spento di default): GlucoBar passa il valore ad altri dispositivi della
rete di casa, così luci, display con ESP32, Home Assistant, Stream Deck o OBS lo
possono mostrare senza conoscere la password del sensore.

- HTTP: un piccolo server sul computer. /api/v1/current dà il valore in JSON; gli
  indirizzi di Nightscout (/api/v1/entries.json, /api/v1/status.json) funzionano come
  quelli di un sito Nightscout, così i display già pensati per Nightscout leggono da
  GlucoBar; /overlay è una pagina per OBS. Di default risponde solo a questo computer;
  per gli altri dispositivi va aperto alla rete locale, volendo con una chiave.
- MQTT: pubblica il valore su un broker (per esempio quello di Home Assistant), con
  la scoperta automatica dei sensori di Home Assistant.

Il server e il client MQTT girano in thread loro: leggono solo `snapshot`, preparato dal
thread di Tk e sostituito tutto insieme a ogni aggiornamento."""

import hashlib
import json
import queue
import re
import select
import socket
import struct
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__, credentials, stats
from .config import log
from .sources import TREND_ARROWS
from .theme import palette

PORT = 17580
# frecce numeriche di LibreLinkUp -> nomi di Nightscout (Dexcom e Nightscout li hanno già)
DIRECTIONS = {1: "SingleDown", 2: "FortyFiveDown", 3: "Flat", 4: "FortyFiveUp", 5: "SingleUp"}


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat().replace("+00:00", "Z")


def state_of(cfg, mgdl, stale):
    if stale:
        return "stale"
    if mgdl < cfg["low"]:
        return "low"
    if mgdl > cfg["very_high"]:
        return "very_high"
    return "high" if mgdl > cfg["high"] else "in_range"


def display_value(cfg, mgdl):
    return round(mgdl / 18.016, 1) if cfg["unit"] == "mmol/L" else int(round(mgdl))


def person(cfg, key, name, primary, current, history=None, now=None):
    """Il valore di una persona come lo vede chi lo chiede: numeri, colore, stato."""
    now = now or time.time()
    mgdl = current["mgdl"]
    stale = (now - current["time"]) / 60 >= cfg["stale_minutes"]
    pal = palette(cfg, light=False)
    delta = stats.delta(history or [], current)
    trend = current.get("trend")
    data = {
        "id": key, "name": name, "primary": primary,
        "value": display_value(cfg, mgdl), "unit": cfg["unit"], "mgdl": mgdl,
        "trend": DIRECTIONS.get(trend, trend), "arrow": TREND_ARROWS.get(trend, ""),
        "delta": None if delta is None else round(delta, 1),
        "time": iso(current["time"]), "timestamp": int(current["time"] * 1000),
        "age_minutes": max(0, int((now - current["time"]) // 60)),
        "stale": stale, "state": state_of(cfg, mgdl, stale),
        "color": pal.stale if stale else pal.value(cfg, mgdl),
    }
    if history is not None:
        data["history"] = [{"mgdl": m["mgdl"], "timestamp": int(m["time"] * 1000)}
                           for m in history if m.get("mgdl")]
    return data


def make_snapshot(ctl, now=None):
    """Tutto quello che il ponte può dare, dal controller (thread di Tk)."""
    cfg = ctl.cfg
    people = []
    if ctl.current:
        people.append(person(cfg, ctl.person_key(), ctl.person_label(), True,
                             ctl.current, ctl.history, now))
    for other in ctl.others:
        people.append(person(cfg, ctl.person_key(other["id"]), other["label"], False,
                             other["current"], None, now))
    return {"unit": cfg["unit"], "people": people, "error": ctl.error,
            "thresholds": {"low": cfg["low"], "high": cfg["high"], "very_high": cfg["very_high"]}}


def slug(text):
    return re.sub(r"[^a-z0-9_]+", "_", str(text).lower()).strip("_")[:24] or "main"


def local_address():
    """L'indirizzo di questo computer nella rete di casa (per gli altri dispositivi)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9))   # nessun pacchetto parte: serve solo a sceglierlo
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


# ---- HTTP ----

OVERLAY = """<!doctype html>
<html><head><meta charset="utf-8"><title>GlucoBar</title>
<style>
  html, body { margin: 0; background: transparent; font-family: "Segoe UI", system-ui, sans-serif; }
  #v { font-size: SIZEpx; font-weight: 700; color: #3ecf6e; text-shadow: 0 2px 6px rgba(0,0,0,.6); }
  #m { font-size: calc(SIZEpx * .3); color: #e6e7ea; text-shadow: 0 1px 4px rgba(0,0,0,.7); }
</style></head>
<body><div id="v">--</div><div id="m"></div>
<script>
  async function load() {
    try {
      const r = await fetch("api/v1/current" + location.search);
      const p = await r.json();
      const v = document.getElementById("v");
      v.textContent = p.value + " " + p.arrow;
      v.style.color = p.color;
      document.getElementById("m").textContent =
        (p.primary ? "" : p.name + " · ") + p.unit + " · " + p.age_minutes + " min";
    } catch (e) {}
  }
  load(); setInterval(load, 10000);
</script></body></html>"""

HELP = """<!doctype html>
<html><head><meta charset="utf-8"><title>GlucoBar</title>
<style>body {{ font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; line-height: 1.5; }}
code {{ background: #eee; padding: 1px 4px; }}</style></head>
<body><h1>GlucoBar {version}</h1>
<p>Local bridge. Not a medical device.</p>
<ul>
<li><a href="api/v1/current{q}"><code>/api/v1/current</code></a>: the current value (JSON)</li>
<li><a href="api/v1/people{q}"><code>/api/v1/people</code></a>: everyone shown in GlucoBar</li>
<li><a href="api/v1/history{q}"><code>/api/v1/history</code></a>: the last hours</li>
<li><a href="api/v1/entries.json{q}"><code>/api/v1/entries.json</code></a> and
  <a href="api/v1/status.json{q}"><code>/api/v1/status.json</code></a>: like a Nightscout site</li>
<li><a href="overlay{q}"><code>/overlay</code></a>: a page for OBS (browser source)</li>
</ul></body></html>"""


class Server(ThreadingHTTPServer):
    # niente SO_REUSEADDR: su Windows permetterebbe di prendere la porta di un altro
    # programma che la sta già usando
    allow_reuse_address = False
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    bridge = None   # impostato da Bridge

    def log_message(self, *args):
        pass

    def send(self, code, body, content_type="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, obj, code=200):
        self.send(code, json.dumps(obj, ensure_ascii=False))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "api-secret, authorization")
        self.end_headers()

    def authorized(self, query):
        token = self.bridge.token()
        if not token:
            return True
        hashed = hashlib.sha1(token.encode()).hexdigest()
        offered = [query.get("token", [""])[0], self.headers.get("api-secret", ""),
                   (self.headers.get("Authorization") or "").replace("Bearer ", "", 1)]
        return any(o and o in (token, hashed) for o in offered)

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        query = urllib.parse.parse_qs(url.query)
        path = url.path.rstrip("/") or "/"
        if not self.authorized(query):
            return self.send_json({"error": "unauthorized"}, 401)
        snap = self.bridge.snapshot
        people = snap["people"]
        if path == "/":
            q = f"?token={urllib.parse.quote(query['token'][0])}" if "token" in query else ""
            return self.send(200, HELP.format(version=__version__, q=q), "text/html")
        if path == "/overlay":
            size = query.get("size", ["64"])[0]
            size = size if size.isdigit() else "64"
            return self.send(200, OVERLAY.replace("SIZE", size), "text/html")
        if path == "/api/v1/people":
            return self.send_json([without_history(p) for p in people])
        wanted = choose(people, query.get("person", [""])[0])
        if path in ("/api/v1/current", "/api/v1/current.json"):
            if not wanted:
                return self.send_json({"error": snap["error"] or "no data"}, 503)
            return self.send_json(without_history(wanted))
        if path in ("/api/v1/history", "/api/v1/history.json"):
            hours = number(query.get("hours", ["24"])[0], 24, 1, 48)
            since = (time.time() - hours * 3600) * 1000
            history = (wanted or {}).get("history") or []
            return self.send_json([m for m in history if m["timestamp"] >= since])
        if path in ("/api/v1/entries", "/api/v1/entries.json", "/api/v1/entries/sgv",
                    "/api/v1/entries/sgv.json", "/api/v1/entries/current",
                    "/api/v1/entries/current.json"):
            count = 1 if "current" in path else number(query.get("count", ["10"])[0], 10, 1, 1000)
            return self.send_json(nightscout_entries(wanted, count))
        if path in ("/api/v1/status", "/api/v1/status.json"):
            return self.send_json(nightscout_status(snap))
        return self.send_json({"error": "not found"}, 404)


def without_history(p):
    return {k: v for k, v in p.items() if k != "history"}


def choose(people, wanted):
    """La persona chiesta (?person=nome, id o numero da 0), altrimenti la principale."""
    if not people:
        return None
    if wanted:
        for i, p in enumerate(people):
            if wanted.lower() in (str(i), str(p["id"]).lower(), str(p["name"]).lower()):
                return p
    return people[0]


def number(text, default, low, high):
    try:
        return max(low, min(high, int(text)))
    except ValueError:
        return default


def nightscout_entries(p, count):
    """Le letture come le dà un sito Nightscout (dalla più recente)."""
    if not p:
        return []
    readings = p.get("history") or [{"mgdl": p["mgdl"], "timestamp": p["timestamp"]}]
    readings = sorted(readings, key=lambda m: m["timestamp"], reverse=True)[:count]
    entries = []
    for i, m in enumerate(readings):
        latest = i == 0 and m["timestamp"] == p["timestamp"]
        entries.append({
            "_id": f"glucobar{m['timestamp']}", "type": "sgv", "sgv": m["mgdl"],
            "date": m["timestamp"], "dateString": iso(m["timestamp"] / 1000),
            "sysTime": iso(m["timestamp"] / 1000),
            "direction": p["trend"] if latest else "NONE",
            "delta": p["delta"] if latest else None, "device": "GlucoBar"})
    return entries


def nightscout_status(snap):
    t = snap["thresholds"]
    return {"status": "ok", "name": "GlucoBar", "version": __version__,
            "serverTime": iso(time.time()), "apiEnabled": True,
            "settings": {"units": "mmol" if snap["unit"] == "mmol/L" else "mg/dl",
                         "thresholds": {"bgHigh": t["very_high"], "bgTargetTop": t["high"],
                                        "bgTargetBottom": t["low"], "bgLow": t["low"]}}}


# ---- MQTT (3.1.1, solo pubblicazione: bastano poche righe, senza librerie) ----

def _length(n):
    out = bytearray()
    while True:
        byte, n = n % 128, n // 128
        out.append(byte | 0x80 if n else byte)
        if not n:
            return bytes(out)


def _text(s):
    data = s.encode("utf-8")
    return struct.pack("!H", len(data)) + data


def connect_packet(client_id, user="", password="", will=None, keepalive=60):
    flags = 0x02                                   # sessione pulita
    payload = _text(client_id)
    if will:
        flags |= 0x04 | 0x20                       # ultimo messaggio, conservato
        payload += _text(will[0]) + _text(will[1])
    if user:
        flags |= 0x80
        payload += _text(user)
        if password:
            flags |= 0x40
            payload += _text(password)
    body = _text("MQTT") + bytes([4, flags]) + struct.pack("!H", keepalive) + payload
    return bytes([0x10]) + _length(len(body)) + body


def publish_packet(topic, payload, retain=True):
    body = _text(topic) + payload.encode("utf-8")
    return bytes([0x30 | (0x01 if retain else 0)]) + _length(len(body)) + body


class Mqtt:
    """Pubblica l'ultimo snapshot su un broker; si riconnette da solo."""

    def __init__(self, cfg):
        self.cfg = dict(cfg)
        self.queue = queue.Queue()
        self.status = "…"
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    @property
    def base(self):
        return (self.cfg.get("mqtt_topic") or "glucobar").strip("/")

    def push(self, snap):
        self.queue.put(snap)

    def stop(self):
        self.stopped.set()
        self.queue.put(None)

    def run(self):
        delay = 5
        while not self.stopped.is_set():
            try:
                self.session()
                delay = 5
            except (OSError, ValueError) as e:
                self.status = f"error: {e}"
                log(f"MQTT: {e}")
            self.stopped.wait(delay)
            delay = min(delay * 2, 120)

    def session(self):
        cfg = self.cfg
        host = (cfg.get("mqtt_host") or "").strip()
        if not host:
            raise ValueError("no broker address")
        password = credentials.get_password(cfg.get("mqtt_user") or "mqtt", "mqtt") or ""
        sock = socket.create_connection((host, int(cfg.get("mqtt_port") or 1883)), timeout=10)
        try:
            status = f"{self.base}/status"
            sock.sendall(connect_packet(f"glucobar-{slug(socket.gethostname())}",
                                        cfg.get("mqtt_user") or "", password,
                                        will=(status, "offline")))
            reply = sock.recv(4)
            if len(reply) < 4 or reply[0] != 0x20:
                raise ValueError("no answer from the broker")
            if reply[3] != 0:
                raise ValueError({4: "wrong user or password", 5: "not authorized"}.get(
                    reply[3], f"refused ({reply[3]})"))
            sock.sendall(publish_packet(status, "online"))
            self.status = "ok"
            log(f"MQTT collegato a {host}")
            announced, last_ping, last = set(), time.time(), None
            while not self.stopped.is_set():
                try:
                    snap = self.queue.get(timeout=5)
                except queue.Empty:
                    snap = None
                while not self.queue.empty():   # conta solo l'ultimo
                    snap = self.queue.get_nowait() or snap
                if snap and snap is not last:
                    last = snap
                    for p in snap["people"]:
                        key = slug(p["id"])
                        if key not in announced and cfg.get("mqtt_discovery", True):
                            sock.sendall(publish_packet(*self.discovery(p, snap["unit"])))
                            announced.add(key)
                        sock.sendall(publish_packet(f"{self.base}/{key}/state",
                                                    json.dumps(without_history(p))))
                if time.time() - last_ping > 30:
                    sock.sendall(b"\xc0\x00")   # PINGREQ: la connessione resta aperta
                    last_ping = time.time()
                if select.select([sock], [], [], 0)[0] and not sock.recv(256):
                    raise OSError("the broker closed the connection")
            sock.sendall(publish_packet(status, "offline"))
            sock.sendall(b"\xe0\x00")   # DISCONNECT
        finally:
            sock.close()

    def discovery(self, p, unit):
        """Messaggio per Home Assistant: crea da solo il sensore "Glucose <nome>"."""
        key = slug(p["id"])
        state = f"{self.base}/{key}/state"
        config = {
            "name": f"Glucose {p['name']}".strip(), "unique_id": f"glucobar_{key}",
            "object_id": f"glucobar_{key}", "state_topic": state,
            "value_template": "{{ value_json.value }}", "json_attributes_topic": state,
            "unit_of_measurement": unit, "state_class": "measurement", "icon": "mdi:diabetes",
            "availability_topic": f"{self.base}/status",
            "device": {"identifiers": ["glucobar"], "name": "GlucoBar",
                       "manufacturer": "GlucoBar", "sw_version": __version__},
        }
        return f"homeassistant/sensor/glucobar_{key}/config", json.dumps(config)


# ---- insieme ----

class Bridge:
    def __init__(self, ctl):
        self.ctl = ctl
        self.snapshot = {"unit": ctl.cfg["unit"], "people": [], "error": None,
                         "thresholds": {}}
        self.server = None
        self.http_error = None
        self.mqtt = None
        self._http_conf = None
        self._mqtt_conf = None
        self.reconfigure()

    def token(self):
        return (self.ctl.cfg.get("bridge_token") or "").strip()

    def reconfigure(self):
        """Avvia, ferma o riavvia server e MQTT secondo le impostazioni."""
        cfg = self.ctl.cfg
        http_conf = (bool(cfg.get("bridge_http")), int(cfg.get("bridge_port") or PORT),
                     bool(cfg.get("bridge_lan")))
        if http_conf != self._http_conf:
            self._http_conf = http_conf
            self.stop_http()
            if http_conf[0]:
                self.start_http(http_conf[1], "0.0.0.0" if http_conf[2] else "127.0.0.1")
        mqtt_conf = tuple(cfg.get(k) for k in ("mqtt", "mqtt_host", "mqtt_port", "mqtt_user",
                                              "mqtt_topic", "mqtt_discovery"))
        if mqtt_conf != self._mqtt_conf:
            self._mqtt_conf = mqtt_conf
            if self.mqtt:
                self.mqtt.stop()
                self.mqtt = None
            if cfg.get("mqtt"):
                self.mqtt = Mqtt(cfg)
                self.mqtt.push(self.snapshot)

    def start_http(self, port, host):
        handler = type("GlucoBarHandler", (Handler,), {"bridge": self})
        try:
            self.server = Server((host, port), handler)
        except OSError as e:
            self.http_error = str(e)
            log(f"ponte HTTP non avviato su {host}:{port}: {e}")
            return
        self.http_error = None
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        log(f"ponte HTTP su {host}:{port}")

    def stop_http(self):
        if self.server:
            server, self.server = self.server, None
            threading.Thread(target=lambda: (server.shutdown(), server.server_close()),
                             daemon=True).start()

    def addresses(self):
        """Gli indirizzi da usare, per le Impostazioni."""
        if not self.server:
            return []
        port = self.server.server_address[1]
        urls = [f"http://127.0.0.1:{port}"]
        if self.ctl.cfg.get("bridge_lan"):
            urls.insert(0, f"http://{local_address()}:{port}")
        return urls

    def update(self):
        """Dati nuovi (dal thread di Tk): li prepara per server e MQTT."""
        if not (self.server or self.mqtt):
            return
        try:
            self.snapshot = make_snapshot(self.ctl)
        except Exception as e:   # mai fermare GlucoBar per il ponte
            log(f"ponte: {e}")
            return
        if self.mqtt:
            self.mqtt.push(self.snapshot)

    def stop(self):
        self.stop_http()
        if self.mqtt:
            self.mqtt.stop()

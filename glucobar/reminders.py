"""Promemoria (finestra Promemoria, dal clic destro): ritirare i farmaci, ordinare i
sensori, l'insulina lenta a orario fisso... Solo "ricordati di": niente dosi né calcoli.

Ogni promemoria è un dizionario salvato in cfg["reminders"]:
  id, title, kind, time "HH:MM", enabled, created
  kind "daily"     ogni giorno
       "weekly"    days: giorni della settimana (0 = lunedì)
       "interval"  ogni `every` giorni a partire da `date` ("AAAA-MM-GG")
       "once"      una volta sola, il giorno `date`
       "sensor"    `before` giorni prima della fine del sensore (solo FreeStyle Libre)
  fired         l'ultima scadenza già mostrata (per non ripeterla)
  snooze_until  "ricordamelo più tardi"
  done_at       l'ultima volta segnato come fatto
"""

import time
import uuid
from datetime import date, datetime, timedelta

KINDS = ("daily", "weekly", "interval", "once", "sensor")
SNOOZE_MINUTES = (15, 60, 180)
LATE = 12 * 3600   # se il computer era spento all'ora giusta, lo ricorda entro 12 ore
DAY = 86400


def new(title, kind, at="09:00", **fields):
    rem = {"id": uuid.uuid4().hex[:8], "title": title, "kind": kind, "time": at,
           "enabled": True, "created": time.time(), "fired": None, "snooze_until": None,
           "done_at": None}
    rem.update(fields)
    return rem


def valid(rem):
    """Il promemoria ha tutto quello che serve per sapere quando scatta?"""
    try:
        hours, minutes = (int(x) for x in rem["time"].split(":"))
        if not (0 <= hours < 24 and 0 <= minutes < 60) or not rem.get("title", "").strip():
            return False
        kind = rem["kind"]
        if kind == "weekly":
            return bool(rem.get("days")) and all(0 <= d <= 6 for d in rem["days"])
        if kind in ("interval", "once"):
            date.fromisoformat(rem["date"])
            return kind == "once" or int(rem.get("every") or 0) >= 1
        if kind == "sensor":
            return 0 <= int(rem.get("before", 0)) <= 14
        return kind == "daily"
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def _at(day, hhmm):
    hours, minutes = (int(x) for x in hhmm.split(":"))
    return datetime(day.year, day.month, day.day, hours, minutes).timestamp()


def _on(rem, day):
    kind = rem["kind"]
    if kind == "daily":
        return True
    if kind == "weekly":
        return day.weekday() in rem["days"]
    if kind == "interval":
        diff = (day - date.fromisoformat(rem["date"])).days
        return diff >= 0 and diff % int(rem["every"]) == 0
    return False


def _single(rem, sensor_end):
    """La scadenza unica di "once" e "sensor" (None se non si sa)."""
    if rem["kind"] == "once":
        return _at(date.fromisoformat(rem["date"]), rem["time"])
    if not sensor_end:
        return None
    day = date.fromtimestamp(sensor_end) - timedelta(days=int(rem.get("before", 0)))
    return _at(day, rem["time"])


def last_time(rem, now, sensor_end=None):
    """L'ultima scadenza già passata (timestamp), o None."""
    if not valid(rem):
        return None
    if rem["kind"] in ("once", "sensor"):
        ts = _single(rem, sensor_end)
        return ts if ts is not None and ts <= now else None
    today = date.fromtimestamp(now)
    for back in range(0, 400):
        day = today - timedelta(days=back)
        if _on(rem, day):
            ts = _at(day, rem["time"])
            if ts <= now:
                return ts
    return None


def next_time(rem, now, sensor_end=None):
    """La prossima scadenza (timestamp), o None."""
    if not valid(rem):
        return None
    if rem.get("snooze_until") and rem["snooze_until"] > now:
        return rem["snooze_until"]
    if rem["kind"] in ("once", "sensor"):
        ts = _single(rem, sensor_end)
        return ts if ts is not None and ts > now else None
    today = date.fromtimestamp(now)
    for ahead in range(0, 400):
        day = today + timedelta(days=ahead)
        if _on(rem, day):
            ts = _at(day, rem["time"])
            if ts > now:
                return ts
    return None


def due(rem, now, sensor_end=None):
    """Va mostrato adesso?"""
    if not rem.get("enabled", True) or not valid(rem):
        return False
    if rem.get("snooze_until"):
        return now >= rem["snooze_until"]
    ts = last_time(rem, now, sensor_end)
    if ts is None:
        return False
    if ts <= max(rem.get("fired") or 0, rem.get("created") or 0, rem.get("done_at") or 0):
        return False
    return now - ts <= LATE


def fire(rem, now, sensor_end=None):
    """Segna come mostrato (si ripresenta alla scadenza dopo, o dopo un rinvio)."""
    rem["fired"] = last_time(rem, now, sensor_end) or now
    rem["snooze_until"] = None


def done(rem, now):
    rem["done_at"] = now
    rem["snooze_until"] = None


def snooze(rem, now, minutes):
    rem["snooze_until"] = now + minutes * 60


def sensor_end(cfg, life_days):
    """Quando finisce il sensore in uso (dai dati salvati di LibreLinkUp), o None."""
    activated = cfg.get("sensor_activated")
    return activated + life_days * DAY if activated else None

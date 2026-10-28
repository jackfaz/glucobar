"""Il sensore FreeStyle Libre in uso, dai dati di LibreLinkUp (numero di serie e
attivazione): giorni rimasti, promemoria prima della fine e avviso se sembra essersi
fermato prima del tempo, per chiederne la sostituzione.

Dexcom Share e Nightscout non dicono niente del sensore: per loro resta solo la voce
del menu per chiedere la sostituzione."""

import time

DAY = 86400
REMINDERS = (("ending24", 24), ("ending2", 2))   # ore prima della fine
STOPPED_AFTER = 60 * 60   # niente dati da un'ora, con la connessione che funziona...
STOPPED_MIN_LEFT = 12     # ...e più di 12 ore prima della fine prevista
EARLY_DAYS = 1            # sostituito più di un giorno prima della fine


def info(connection):
    """{"sn", "activated", "type"} del sensore attuale, o None se LibreLinkUp non li dà
    ("type" è il campo "pt" di LibreLinkUp: forse il modello, non documentato)."""
    sensor = (connection or {}).get("sensor") or {}
    activated = sensor.get("a")
    if not sensor.get("sn") or not isinstance(activated, (int, float)) or \
            activated < 1_500_000_000:
        return None
    return {"sn": str(sensor["sn"]), "activated": float(activated), "type": sensor.get("pt")}


def life_days(cfg):
    try:
        return min(max(int(cfg.get("sensor_life_days") or 14), 7), 15)
    except (TypeError, ValueError):
        return 14


def day_of(sensor, now=None):
    """Giorno di utilizzo, da 1."""
    return int(((now or time.time()) - sensor["activated"]) // DAY) + 1


def hours_left(cfg, sensor, now=None):
    return (sensor["activated"] + life_days(cfg) * DAY - (now or time.time())) / 3600


class SensorWatch:
    """Ricorda il sensore in cfg (sensor_sn, sensor_activated, sensor_notified) per
    accorgersi del cambio anche tra un avvio e l'altro e non ripetere gli avvisi."""

    def check(self, cfg, connection, current, error, now=None):
        """(eventi da mostrare [(nome, dati)], cfg cambiato e da salvare)."""
        now = now or time.time()
        sensor = info(connection)
        if not sensor:
            return [], False
        events, dirty = [], False
        if cfg.get("sensor_sn") != sensor["sn"]:
            old_sn, old_activated = cfg.get("sensor_sn"), cfg.get("sensor_activated")
            if old_sn and old_activated:
                lasted = (sensor["activated"] - old_activated) / DAY
                if lasted < life_days(cfg) - EARLY_DAYS:
                    events.append(("replaced_early", {"sn": old_sn, "days": max(0, int(lasted))}))
            cfg.update(sensor_sn=sensor["sn"], sensor_activated=sensor["activated"],
                       sensor_notified=[])
            dirty = True
        notified = set(cfg.get("sensor_notified") or [])
        left = hours_left(cfg, sensor, now)
        due = [key for key, hours in REMINDERS if 0 < left <= hours]
        if due and due[-1] not in notified:   # un solo promemoria: il più vicino alla fine
            notified.update(due)
            events.append(("ending", {"hours": left}))
        if (current and not error and now - current["time"] >= STOPPED_AFTER
                and left > STOPPED_MIN_LEFT and "stopped" not in notified):
            notified.add("stopped")
            events.append(("stopped", {"sn": sensor["sn"]}))
        if events:
            cfg["sensor_notified"] = sorted(notified)
            dirty = True
        return events, dirty

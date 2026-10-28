"""Statistiche sulle ultime ore di misure, per la modalità "sfondo"."""

import time


def recent(history, hours, now=None):
    """Misure delle ultime `hours` ore, in ordine di tempo."""
    now = now or time.time()
    start = now - hours * 3600
    return sorted((m for m in history if m["mgdl"] and m["time"] >= start),
                  key=lambda m: m["time"])


def summary(points, cfg):
    """Media, minimo, massimo e percentuali sotto/nel/sopra il range.
    None se non ci sono misure."""
    if not points:
        return None
    values = [m["mgdl"] for m in points]
    n = len(values)
    below = sum(v < cfg["low"] for v in values)
    above = sum(v > cfg["high"] for v in values)
    return {
        "mean": sum(values) / n,
        "min": min(values),
        "max": max(values),
        "below": 100 * below / n,
        "in_range": 100 * (n - below - above) / n,
        "above": 100 * above / n,
        "count": n,
    }


def change(points, current, minutes=15, tolerance=6):
    """Variazione in mg/dL rispetto a `minutes` minuti fa (None se non c'è
    una misura abbastanza vicina a quel momento)."""
    target = current["time"] - minutes * 60
    best = min(points, key=lambda m: abs(m["time"] - target), default=None)
    if best is None or abs(best["time"] - target) > tolerance * 60:
        return None
    return current["mgdl"] - best["mgdl"]


def delta(history, current, oldest=20):
    """Il "delta" dei CGM: variazione rispetto alla lettura precedente, riportata a
    5 minuti come fa Nightscout (Dexcom legge ogni 5 minuti; LibreLinkUp nello storico
    ha un punto ogni 15). None se non c'è una lettura precedente negli ultimi `oldest`
    minuti."""
    before = [m for m in history if m["mgdl"]
              and 60 <= current["time"] - m["time"] <= oldest * 60]
    if not before:
        return None
    previous = max(before, key=lambda m: m["time"])
    return (current["mgdl"] - previous["mgdl"]) * 300 / (current["time"] - previous["time"])


def sensor_days(connection, now=None):
    """Giorni da quando il sensore è stato attivato, se LibreLinkUp lo dice."""
    activated = ((connection or {}).get("sensor") or {}).get("a")
    if not isinstance(activated, (int, float)) or activated < 1_500_000_000:
        return None
    return ((now or time.time()) - activated) / 86400

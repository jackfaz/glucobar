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


def delta(history, current, oldest=7):
    """Il "delta": il valore attuale meno la lettura precedente, come lo mostrano le app
    dei sensori. Con Dexcom e Nightscout la precedente è di 5 minuti prima; con
    LibreLinkUp, che ha un valore nuovo ogni minuto, è quella del minuto prima (vedi
    with_live). None se non c'è una lettura negli ultimi `oldest` minuti: meglio niente
    che un numero sbagliato.

    Fino alla 0.11.5 la variazione veniva riportata a 5 minuti: con letture a un minuto
    di distanza un +2 diventava +10, e un punto "storico" di LibreLinkUp poteva dare un
    +9 a valore fermo."""
    before = [m for m in history if m["mgdl"]
              and 30 <= current["time"] - m["time"] <= oldest * 60]
    if not before:
        return None
    previous = max(before, key=lambda m: m["time"])
    return current["mgdl"] - previous["mgdl"]


def delta_per_5min(history, current):
    """La variazione riportata a 5 minuti, come il "delta" di Nightscout (per le app e i
    display collegati al ponte locale): rispetto alla lettura più vicina a 5 minuti
    prima, tra 3 e 10 minuti."""
    before = [m for m in history if m["mgdl"]
              and 180 <= current["time"] - m["time"] <= 600]
    if not before:
        return None
    previous = min(before, key=lambda m: abs(current["time"] - m["time"] - 300))
    return (current["mgdl"] - previous["mgdl"]) * 300 / (current["time"] - previous["time"])


def keep_live(live, current, minutes=30):
    """I valori attuali ricevuti negli ultimi `minutes` minuti, con quello nuovo."""
    start = current["time"] - minutes * 60
    return [m for m in live if start <= m["time"] < current["time"]] + [current]


def with_live(history, live):
    """Lo storico con, per il tratto più recente, i valori in tempo reale ricevuti da
    GlucoBar. LibreLinkUp nello storico ha un punto ogni 15 minuti con i valori
    "storici" del sensore, un po' diversi da quelli in tempo reale: da quando ci sono
    valori in tempo reale si usano solo quelli, così il delta confronta valori dello
    stesso tipo."""
    if not live:
        return history
    start = live[0]["time"] - 30
    past = [m for m in history if m["time"] < start]
    return sorted(past, key=lambda m: m["time"]) + list(live)


def sensor_days(connection, now=None):
    """Giorni da quando il sensore è stato attivato, se LibreLinkUp lo dice."""
    activated = ((connection or {}).get("sensor") or {}).get("a")
    if not isinstance(activated, (int, float)) or activated < 1_500_000_000:
        return None
    return ((now or time.time()) - activated) / 86400


PREDICT_MINUTES = 30


def predict(history, current, ahead=PREDICT_MINUTES, window=30, now=None):
    """Stima della tendenza: una retta tra le letture degli ultimi `window` minuti,
    prolungata di `ahead` minuti. Non sa niente di cibo, insulina o attività fisica: è
    solo dove andrebbe il valore se continuasse come adesso, e spesso sbaglia.

    Ritorna {"slope": mg/dL al minuto, "points": [(minuti, valore, basso, alto)], ...}
    con la fascia di incertezza che si allarga col tempo, oppure None se le letture
    sono troppo poche, troppo vicine tra loro o vecchie."""
    now = now or time.time()
    if not current or not current.get("mgdl") or now - current["time"] > 10 * 60:
        return None
    t0 = current["time"]
    pts = {round(m["time"]): m["mgdl"] for m in history
           if m.get("mgdl") and 0 <= t0 - m["time"] <= window * 60}
    pts[round(t0)] = current["mgdl"]
    if len(pts) < 2:
        return None
    xs = [(ts - t0) / 60 for ts in pts]          # minuti, <= 0
    ys = list(pts.values())
    if -min(xs) < 9:
        return None   # letture troppo vicine: la pendenza sarebbe solo rumore
    # le letture recenti contano di più
    ws = [1 + (x + window) / window for x in xs]
    sw = sum(ws)
    mx = sum(w * x for w, x in zip(ws, xs)) / sw
    my = sum(w * y for w, y in zip(ws, ys)) / sw
    var = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
    slope = sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys)) / var
    slope = max(-4.0, min(4.0, slope))   # oltre 4 mg/dL al minuto è quasi sempre un errore
    # partenza dal valore attuale, non dalla retta: è quello che si vede
    noise = (sum(w * (y - (my + slope * (x - mx))) ** 2
                 for w, x, y in zip(ws, xs, ys)) / sw) ** 0.5
    points = []
    for minutes in range(5, ahead + 1, 5):
        value = current["mgdl"] + slope * minutes
        spread = max(6.0, noise) + 0.6 * minutes
        points.append((minutes, clamp(value), clamp(value - spread), clamp(value + spread)))
    return {"slope": slope, "points": points, "from": current["mgdl"], "time": t0}


def clamp(value, low=40, high=400):
    return max(low, min(high, value))


def minutes_to(prediction, threshold):
    """Fra quanti minuti la retta della stima scende sotto `threshold` (None se non ci
    arriva entro la stima)."""
    if not prediction or prediction["slope"] >= 0 or prediction["from"] < threshold:
        return None
    minutes = (prediction["from"] - threshold) / -prediction["slope"]
    return minutes if minutes <= prediction["points"][-1][0] else None

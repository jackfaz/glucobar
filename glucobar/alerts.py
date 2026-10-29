"""Avvisi facoltativi (spenti di default): valore basso, molto alto, nessun dato.
Non sostituiscono gli allarmi del sensore: GlucoBar legge i dati da un servizio
online, con qualche minuto di ritardo, e solo quando il computer è acceso.

Ogni avviso arriva una volta per episodio: di nuovo solo dopo che il valore è
tornato nella norma (o è arrivato un dato nuovo)."""

import time

from . import stats

# "soon": la stima della tendenza (stats.predict) scende sotto la soglia bassa
KINDS = ("low", "high", "stale", "soon")


def soon_minutes(cfg, history, current, now=None):
    """Fra quanti minuti la stima della tendenza va sotto la soglia bassa, o None."""
    if not current or not current.get("mgdl") or current["mgdl"] < cfg["low"]:
        return None
    return stats.minutes_to(stats.predict(history or [], current, now=now), cfg["low"])


def conditions(cfg, current, now=None, history=None):
    if not current:
        return dict.fromkeys(KINDS, False)
    now = now or time.time()
    stale = (now - current["time"]) / 60 >= cfg["stale_minutes"]
    mgdl = current["mgdl"] or 0
    return {
        "low": not stale and 0 < mgdl < cfg["low"],
        "high": not stale and mgdl > cfg["very_high"],
        "stale": stale,
        "soon": not stale and soon_minutes(cfg, history, current, now) is not None,
    }


class AlertWatch:
    def __init__(self):
        self.active = set()   # avvisi già dati per l'episodio in corso

    def check(self, cfg, current, now=None, history=None):
        """Avvisi da dare adesso, tra quelli accesi in cfg (alert_low, ...)."""
        cond = conditions(cfg, current, now, history)
        on = {kind for kind in KINDS if cond[kind] and cfg.get(f"alert_{kind}")}
        new = [kind for kind in KINDS if kind in on and kind not in self.active]
        self.active = on
        return new

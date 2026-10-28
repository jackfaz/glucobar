"""Avvisi facoltativi (spenti di default): valore basso, molto alto, nessun dato.
Non sostituiscono gli allarmi del sensore: GlucoBar legge i dati da un servizio
online, con qualche minuto di ritardo, e solo quando il computer è acceso.

Ogni avviso arriva una volta per episodio: di nuovo solo dopo che il valore è
tornato nella norma (o è arrivato un dato nuovo)."""

import time

KINDS = ("low", "high", "stale")


def conditions(cfg, current, now=None):
    if not current:
        return dict.fromkeys(KINDS, False)
    now = now or time.time()
    stale = (now - current["time"]) / 60 >= cfg["stale_minutes"]
    mgdl = current["mgdl"] or 0
    return {
        "low": not stale and 0 < mgdl < cfg["low"],
        "high": not stale and mgdl > cfg["very_high"],
        "stale": stale,
    }


class AlertWatch:
    def __init__(self):
        self.active = set()   # avvisi già dati per l'episodio in corso

    def check(self, cfg, current, now=None):
        """Avvisi da dare adesso, tra quelli accesi in cfg (alert_low, ...)."""
        cond = conditions(cfg, current, now)
        on = {kind for kind in KINDS if cond[kind] and cfg.get(f"alert_{kind}")}
        new = [kind for kind in KINDS if kind in on and kind not in self.active]
        self.active = on
        return new

"""Da dove arrivano le letture: LibreLinkUp (FreeStyle Libre), Dexcom Share o un sito
Nightscout.

Ogni client ha `fetch()` -> (misura_corrente, storico), con le misure nel formato
{mgdl, trend, time}, e `connection` (dati del sensore, se il servizio li dà).
"""

from .i18n import t

SOURCES = ("libre", "dexcom", "nightscout")
# per Nightscout l'"account" (cfg["email"]) è l'indirizzo del sito e il token è facoltativo
OPTIONAL_SECRET = {"nightscout"}
DEXCOM_REGIONS = ("ous", "us", "jp")   # fuori dagli USA, USA, Giappone

# Tendenza -> freccia: numeri 1-5 di LibreLinkUp, nomi di Dexcom Share e Nightscout
TREND_ARROWS = {
    1: "↓", 2: "↘", 3: "→", 4: "↗", 5: "↑",
    "DoubleUp": "↑↑", "SingleUp": "↑", "FortyFiveUp": "↗", "Flat": "→",
    "FortyFiveDown": "↘", "SingleDown": "↓", "DoubleDown": "↓↓",
}


class SourceError(Exception):
    """Errore da mostrare così com'è (già tradotto)."""


def source_options():
    """[(sorgente, testo)] per le domande "quale sensore usi?"."""
    return [(source, t(f"sensor_{source}")) for source in SOURCES]


def region_options():
    return [(region, t(f"region_{region}")) for region in DEXCOM_REGIONS]


def account_ready(cfg):
    """C'è tutto quello che serve per leggere i dati senza chiedere niente?"""
    from . import credentials
    if not cfg.get("email"):
        return False
    source = cfg.get("source", "libre")
    return source in OPTIONAL_SECRET or bool(credentials.get_password(cfg["email"], source))


def make_client(cfg, **kwargs):
    if cfg.get("source") == "dexcom":
        from .dexcom import DexcomShare
        return DexcomShare(cfg, **kwargs)
    if cfg.get("source") == "nightscout":
        from .nightscout import Nightscout
        return Nightscout(cfg, **kwargs)
    from .librelinkup import LibreLinkUp
    return LibreLinkUp(cfg, **kwargs)


def fetch_safely(client):
    """(misura, storico, errore): mai eccezioni, per i thread delle interfacce."""
    try:
        current, history = client.fetch()
        return current, history, None
    except SourceError as e:
        return None, None, str(e)
    except Exception as e:  # risposta in formato imprevisto, ecc.
        return None, None, t("err_generic", msg=e)

"""Dove chiedere la sostituzione di un sensore che si è fermato prima del tempo: la
pagina ufficiale del produttore per il paese dell'utente (impostazioni internazionali
di Windows o macOS), oppure quella internazionale."""

import os
import sys

ABBOTT = "https://www.freestyle.abbott"
DEXCOM = "https://www.dexcom.com"

# paese -> modulo di Abbott per FreeStyle Libre (in Svizzera, Belgio e Canada dipende
# anche dalla lingua: chiave "paese-lingua")
LIBRE_FORMS = {
    "IT": ABBOTT + "/it-it/support/sensor-support-form.html",
    "US": ABBOTT + "/us-en/support/sensorsupportrequest.html",
    "GB": ABBOTT + "/uk-en/support/sensor-support-form.html",
    "IE": ABBOTT + "/ie-en/support/sensor-support-form.html",
    "CA": ABBOTT + "/en-ca/support/guided-questions.html",
    "CA-fr": ABBOTT + "/fr-ca/support/guided-questions.html",
    "ES": ABBOTT + "/es-es/ayuda/reemplazo-sensor.html",
    "MX": ABBOTT + "/es-mx/support/sensor-support-form.html",
    "FR": "https://freestyle.abbott/fr-fr/support/formulaire-de-demande-de-remplacement.html",
    "BE": ABBOTT + "/be-fr/support/sensor-support-form.html",
    "CH": ABBOTT + "/ch-de/hilfe/sensor-support-form.html",
    "CH-fr": ABBOTT + "/ch-fr/assistance/sensor-support-form.html",
    "CH-it": ABBOTT + "/ch-it/supporto/sensor-support-form.html",
    "AT": ABBOTT + "/at-de/support/sensor-support-form.html",
    "PT": ABBOTT + "/pt-pt/suporte/formulario-de-pedido-de-substituicao-do-sensor.html",
}
LIBRE_FALLBACK = ABBOTT + "/"   # scelta del paese

# paese -> pagina di Dexcom su come chiedere la sostituzione
DEXCOM_PAGES = {
    "US": DEXCOM + "/en-us/faqs/general/sensor-replacement",
    "GB": DEXCOM + "/en-gb/faqs/general/sensor-replacement",
    "IE": DEXCOM + "/en-ie/sensor-replacement-policy",
    "CA": DEXCOM + "/en-ca/faqs/g7/how-to-get-a-replacement-dexcom-g7-sensor",
    "CA-fr": DEXCOM + "/fr-ca/faqs/g7/comment-puis-je-obtenir-un-remplacement-pour-le-capteur-dexcom-g7",
    "AU": DEXCOM + "/en-au/sensor-replacement-policy",
    "ES": DEXCOM + "/es-es/sensor-replacement-policy",
    "FR": DEXCOM + "/fr-fr/sensor-replacement-policy",
    "BE": DEXCOM + "/fr-be/sensor-replacement-policy",
    "CH": DEXCOM + "/de-ch/sensor-replacement-policy",
    "CH-fr": DEXCOM + "/fr-ch/sensor-replacement-policy",
    "CH-it": DEXCOM + "/it-ch/sensor-replacement-policy",
    "DE": DEXCOM + "/de-de/sensor-replacement-policy",
    "AT": DEXCOM + "/de-at/sensor-replacement-policy",
}
DEXCOM_FALLBACK = DEXCOM + "/sensor-replacement-policy"

MAKERS = ("libre", "dexcom")


def _windows_locale():
    import ctypes
    buf = ctypes.create_unicode_buffer(85)
    if ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85):
        return buf.value          # es. "it-IT"
    return ""


def _mac_locale():
    from Foundation import NSLocale
    return str(NSLocale.currentLocale().localeIdentifier())   # es. "it_IT"


def user_locale():
    """(lingua, PAESE) delle impostazioni internazionali, es. ("it", "IT")."""
    try:
        if sys.platform == "win32":
            name = _windows_locale()
        elif sys.platform == "darwin":
            name = _mac_locale()
        else:
            name = os.environ.get("LC_ALL") or os.environ.get("LANG") or ""
    except Exception:
        name = ""
    parts = name.split(".")[0].replace("_", "-").split("-")
    lang = parts[0].lower() if parts and parts[0] else ""
    country = next((p.upper() for p in parts[1:] if len(p) == 2), "")
    return lang, country


def replacement_url(maker, locale=None):
    lang, country = locale or user_locale()
    pages, fallback = (DEXCOM_PAGES, DEXCOM_FALLBACK) if maker == "dexcom" else \
        (LIBRE_FORMS, LIBRE_FALLBACK)
    return pages.get(f"{country}-{lang}") or pages.get(country) or fallback

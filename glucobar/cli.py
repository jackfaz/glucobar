"""Il comando `glucobar` da terminale (glucobar-cli.exe, richiamato da bin\\glucobar.cmd).

    glucobar setup                configurazione guidata, con le frecce
    glucobar status               glicemia attuale nel terminale
    glucobar set unit=mmol/L ...  cambia impostazioni (anche per script)
    glucobar get [chiave ...]     mostra le impostazioni
    glucobar login                cambia sensore o account
    glucobar start                avvia GlucoBar
    glucobar stop                 chiude GlucoBar
    glucobar forget               cancella password e impostazioni
    glucobar report               riepilogo per le segnalazioni (copiato negli appunti)

Se GlucoBar è aperto, si accorge da solo delle impostazioni cambiate.
"""

import argparse
import os
import subprocess
import sys

from . import __version__, autostart, credentials, i18n, instance, tui
from .config import CONFIG_PATH, ELEMENTS, MIN_REFRESH, forget_everything, load_config, \
    normalize_elements, save_config
from .i18n import LANGUAGES, element_name, t
from .theme import PALETTES, THEMES
from .nightscout import normalize_url
from .sources import DEXCOM_REGIONS, SOURCES, TREND_ARROWS, account_ready, fetch_safely, \
    make_client, region_options, source_options
from .ui_common import age_minutes, fmt_value


# ---- impostazioni modificabili con "glucobar set" ----
def _int(lo, hi):
    def parse(raw):
        value = int(raw)
        if not lo <= value <= hi:
            raise ValueError(f"must be between {lo} and {hi}")
        return value
    return parse


def _float(lo, hi):
    def parse(raw):
        value = float(raw)
        if not lo <= value <= hi:
            raise ValueError(f"must be between {lo} and {hi}")
        return value
    return parse


def _choice(*choices):
    def parse(raw):
        for choice in choices:
            if raw.lower() == str(choice).lower():
                return choice
        raise ValueError(f"must be one of: {', '.join(map(str, choices))}")
    return parse


def _bool(raw):
    low = raw.lower()
    if low in ("1", "true", "yes", "on", "si", "sì"):
        return True
    if low in ("0", "false", "no", "off"):
        return False
    raise ValueError("must be true or false")


def _elements(raw):
    items = [e.strip() for e in raw.split(",") if e.strip()]
    wrong = [e for e in items if e not in ELEMENTS]
    if wrong or not items:
        raise ValueError(f"comma-separated list of: {', '.join(ELEMENTS)}")
    return normalize_elements(items)


def _color(raw):
    if raw.lower() in ("auto", "none", ""):
        return None
    if len(raw) == 7 and raw[0] == "#" and all(c in "0123456789abcdefABCDEF" for c in raw[1:]):
        return raw.lower()
    raise ValueError("must be a colour like #202020, or auto")


SETTINGS = {
    "source": _choice(*SOURCES),
    "dexcom_region": _choice(*DEXCOM_REGIONS),
    "elements": _elements,
    "language": _choice("auto", *LANGUAGES),
    "unit": _choice("mg/dL", "mmol/L"),
    "low": _int(40, 200),
    "high": _int(100, 400),
    "very_high": _int(150, 500),
    "stale_minutes": _int(5, 120),
    "refresh_seconds": _int(MIN_REFRESH, 3600),
    "taskbar_monitor": _int(1, 9),
    "taskbar_side": _choice("right", "left"),
    "taskbar_offset": _int(-3000, 3000),
    "taskbar_transparent": _bool,
    "taskbar_bg": _color,
    "taskbar_scale": _float(0.7, 1.25),
    "window_scale": _float(0.8, 2.5),
    "desktop_hours": lambda raw: _choice(3, 6, 12)(raw),
    "desktop_alpha": _float(0.3, 1.0),
    "desktop_locked": _bool,
    "desktop_on_top": _bool,
    "desktop_over_fullscreen": _bool,
    "theme": _choice(*THEMES),
    "palette": _choice(*PALETTES),
    "color_in_range": _color,
    "color_high": _color,
    "color_very_high": _color,
    "color_low": _color,
    "color_stale": _color,
    "taskbar_text": _color,
    "alert_low": _bool,
    "alert_high": _bool,
    "alert_stale": _bool,
    "update_check": _bool,
    "show_delta": _bool,
    "hover_chart": _bool,
    "auto_update": _bool,
    "sensor_life_days": _int(10, 15),
    "autostart": _bool,   # nel registro di Windows, non in config.json
}


def parse_assignments(pairs, cfg):
    """["unit=mmol/L", "low=80"] -> {"unit": "mmol/L", "low": 80}; ValueError se no."""
    changes = {}
    for pair in pairs:
        key, sep, raw = pair.partition("=")
        key = key.strip().lower()
        if not sep or key not in SETTINGS:
            raise ValueError(f"unknown setting '{key}'. Settings: {', '.join(SETTINGS)}")
        try:
            changes[key] = SETTINGS[key](raw.strip())
        except ValueError as e:
            raise ValueError(f"{key}: {e}") from None
    merged = {**cfg, **changes}
    if not merged["low"] < merged["high"] < merged["very_high"]:
        raise ValueError("thresholds must be low < high < very_high")
    return changes


def show_value(value):
    if isinstance(value, list):
        return ",".join(value)
    if value is None:
        return "auto"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


# ---- GlucoBar aperto? ----
is_running = instance.is_running


def start_gui():
    exe = autostart.gui_exe()
    if exe:
        cmd = [exe]
    else:   # da sorgente
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cmd = [sys.executable, os.path.join(root, "run_glucobar.py")]
    flags = 0x00000008 | 0x00000200 if sys.platform == "win32" else 0  # DETACHED, NEW_GROUP
    subprocess.Popen(cmd, creationflags=flags, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)


def reading_text(cfg, current):
    age = age_minutes(current)
    when = t("now") if age == 0 else t("min_ago", n=age)
    arrow = TREND_ARROWS.get(current["trend"], "")
    return f"{fmt_value(cfg, current['mgdl'])} {arrow} {cfg['unit']} · {when}"


# ---- configurazione guidata ----
def _number(lo, hi):
    def validate(raw):
        try:
            value = int(raw)
        except ValueError:
            value = None
        return None if value is not None and lo <= value <= hi else t("cli_bad_number", a=lo, b=hi)
    return validate


def ask_source(term, cfg):
    """Sensore e, per Dexcom, regione dell'account. Cambia solo `cfg` in memoria:
    si salva alla fine, insieme al resto."""
    hint = t("cli_hint_select")
    tui.message(term, "")
    source = tui.select(term, t("sensor_prompt"), source_options(),
                        default=SOURCES.index(cfg["source"]) if cfg["source"] in SOURCES else 0,
                        hint=hint)
    if source != cfg["source"]:
        cfg["email"] = ""   # l'account di un altro servizio non va riproposto
    cfg["source"] = source
    if source == "dexcom":
        region = cfg["dexcom_region"]
        cfg["dexcom_region"] = tui.select(
            term, t("dexcom_region"), region_options(),
            default=DEXCOM_REGIONS.index(region) if region in DEXCOM_REGIONS else 0, hint=hint)


def ask_account(term, cfg, client_class=None):
    """Account del sensore scelto in `cfg`, con prova di connessione.
    Ritorna (email, password o None)."""
    client_class = client_class or make_client
    source = cfg["source"]
    dexcom, nightscout = source == "dexcom", source == "nightscout"
    if dexcom:   # Dexcom accetta anche telefono e nome utente
        validate = lambda v: None if v.strip() else t("cli_bad_account")  # noqa: E731
    elif nightscout:   # l'indirizzo del sito
        validate = lambda v: None if "." in v and " " not in v.strip() else t("cli_bad_url")  # noqa: E731
    else:
        validate = lambda v: None if "@" in v and "." in v else t("cli_bad_email")  # noqa: E731
    title, label = {"dexcom": ("cli_account_dexcom", "cli_email_dexcom"),
                    "nightscout": ("cli_account_nightscout", "cli_url")}.get(
                        source, ("cli_account", "cli_email"))
    email = cfg.get("email", "")
    while True:
        tui.message(term, "")
        tui.message(term, t(title), tui.BOLD)
        # al nuovo tentativo propone l'email appena scritta
        email = tui.text(term, t(label), default=email,
                         validate=validate, hint=t("cli_hint_text")).strip()
        if nightscout:
            email = normalize_url(email)
        saved = credentials.get_password(email, source)
        if nightscout:   # token facoltativo: i siti pubblici non lo chiedono
            password = tui.text(term, t("cli_token"), secret=True, hint=t("cli_token_hint"))
        else:
            password = tui.text(term, t("cli_password"), secret=True,
                                hint=t("cli_keep_password") if saved else t("cli_hint_text"),
                                validate=lambda v: None if v or saved else t("cli_hint_text"))
        password = password or None   # None = tieni quella salvata
        tui.message(term, t("cli_testing"), tui.DIM)
        trial = {**cfg, "email": email}
        client = client_class(trial, save=lambda _cfg: None, password=password or saved)
        current, _history, error = fetch_safely(client)
        if current:
            tui.message(term, f"{tui.GREEN}{tui.CHECK}{tui.RESET} "
                              + t("cli_test_ok", reading=reading_text(trial, current)))
            # il server può aver indicato regione e versione giuste
            cfg["region"], cfg["app_version"] = trial["region"], trial["app_version"]
            return email, password
        tui.message(term, t("cli_test_fail", error=error), tui.RED)
        if tui.select(term, t("cli_after_fail"), [("retry", t("cli_retry")),
                                                    ("skip", t("cli_skip"))],
                      hint=t("cli_hint_select")) == "skip":
            return email, password


def wizard(term, cfg, client_class=None, monitors=1):
    """Tutte le domande; salva solo alla fine (Ctrl+C/Esc annulla tutto)."""
    tui.message(term, f"{tui.BOLD}GlucoBar {__version__}{tui.RESET} · {t('cli_welcome')}")
    tui.message(term, t("cli_disclaimer"), tui.DIM)
    tui.message(term, "")
    hint = t("cli_hint_select")

    codes = list(LANGUAGES)
    lang = tui.select(term, t("cli_language"), [(c, LANGUAGES[c]) for c in codes],
                      default=codes.index(i18n.current_language()), hint=hint)
    i18n.set_language(lang)
    hint = t("cli_hint_select")   # da qui in poi nella lingua scelta

    elements = tui.multiselect(term, t("cli_show"), [(e, element_name(e)) for e in ELEMENTS],
                               selected=cfg["elements"], hint=t("cli_hint_multi"),
                               need_one=t("cli_need_one"))
    units = ["mg/dL", "mmol/L"]
    unit = tui.select(term, t("cli_unit"), [(u, u) for u in units],
                      default=units.index(cfg["unit"]), hint=hint)

    ranges = []
    if (cfg["low"], cfg["high"]) != (70, 180):
        ranges.append(("keep", t("cli_range_keep", low=cfg["low"], high=cfg["high"])))
    ranges += [("std", t("cli_range_std")), ("custom", t("cli_range_custom"))]
    choice = tui.select(term, t("cli_range"), ranges, hint=hint)
    low, high = cfg["low"], cfg["high"]
    if choice == "std":
        low, high = 70, 180
    elif choice == "custom":
        low = int(tui.text(term, t("cli_low"), default=str(low), validate=_number(40, 150),
                           hint=t("cli_hint_text")))
        high = int(tui.text(term, t("cli_high"), default=str(max(high, low + 10)),
                            validate=_number(low + 10, min(400, cfg["very_high"] - 1)),
                            hint=t("cli_hint_text")))

    monitor = cfg["taskbar_monitor"]
    if "taskbar" in elements and monitors > 1:
        options = [(1, t("cli_monitor_main"))] + [(n, t("cli_monitor_n", n=n))
                                                  for n in range(2, monitors + 1)]
        monitor = tui.select(term, t("cli_monitor"), options,
                             default=min(monitor, monitors) - 1, hint=hint)

    # le scelte valgono già per la prova di connessione (ma si salva solo alla fine)
    cfg.update(language=lang, elements=elements, unit=unit, low=low, high=high,
               taskbar_monitor=monitor)
    ask_source(term, cfg)
    email, password = ask_account(term, cfg, client_class)

    start_with_windows = None
    if autostart.gui_exe():
        tui.message(term, "")
        start_with_windows = tui.confirm(term, t("cli_autostart"), autostart.is_enabled(),
                                         yes=t("cli_yes"), no=t("cli_no"), hint=hint)

    cfg["email"] = email
    save_config(cfg)
    if password:
        credentials.set_password(email, password, cfg["source"])
    if start_with_windows is not None:
        autostart.set_enabled(start_with_windows)
    tui.message(term, "")
    tui.message(term, f"{tui.CHECK} {t('cli_saved')}", tui.GREEN)


def cmd_setup(_args):
    cfg = load_config()
    i18n.set_language(cfg["language"])
    if not tui.Terminal.interactive():
        print(t("cli_not_tty"))
        return 2
    monitors = 1
    if sys.platform == "win32":
        from .taskbar import all_taskbars
        monitors = max(1, len(all_taskbars()))
    try:
        with tui.Terminal() as term:
            wizard(term, cfg, monitors=monitors)
            if is_running():
                tui.message(term, t("cli_applied"))
            elif tui.confirm(term, t("cli_start_now"), True, yes=t("cli_yes"), no=t("cli_no"),
                             hint=t("cli_hint_select")):
                start_gui()
                tui.message(term, t("cli_started"), tui.GREEN)
    except tui.Cancelled:
        print("\n" + t("cli_cancelled"))
        return 130
    return 0


def cmd_login(_args):
    cfg = load_config()
    i18n.set_language(cfg["language"])
    if not tui.Terminal.interactive():
        print(t("cli_not_tty"))
        return 2
    try:
        with tui.Terminal() as term:
            ask_source(term, cfg)
            email, password = ask_account(term, cfg)
            cfg["email"] = email
            save_config(cfg)
            if password:
                credentials.set_password(email, password, cfg["source"])
            tui.message(term, f"{tui.CHECK} {t('cli_saved')}", tui.GREEN)
    except tui.Cancelled:
        print("\n" + t("cli_cancelled"))
        return 130
    return 0


def cmd_status(_args):
    cfg = load_config()
    i18n.set_language(cfg["language"])
    if not account_ready(cfg):
        print(t("cli_no_account"))
        return 1
    current, _history, error = fetch_safely(make_client(cfg))
    if not current:
        print(error)
        return 1
    print(reading_text(cfg, current))
    return 0


def cmd_get(args):
    cfg = load_config()
    keys = args.keys or list(SETTINGS)
    for key in keys:
        if key == "autostart":
            print(f"autostart = {show_value(autostart.is_enabled())}")
        elif key in SETTINGS:
            print(f"{key} = {show_value(cfg[key])}")
        else:
            print(f"unknown setting '{key}'", file=sys.stderr)
            return 2
    if not args.keys:
        print(f"email = {cfg['email'] or '-'}")
        print(f"# {CONFIG_PATH}")
    return 0


def cmd_set(args):
    cfg = load_config()
    try:
        changes = parse_assignments(args.assignments, cfg)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if "autostart" in changes:
        if not autostart.set_enabled(changes.pop("autostart")):
            print("autostart: only available in the installed version on Windows",
                  file=sys.stderr)
            return 1
        print(f"autostart = {show_value(autostart.is_enabled())}")
    cfg.update(changes)
    save_config(cfg)
    for key, value in changes.items():
        print(f"{key} = {show_value(value)}")
    return 0


def cmd_start(_args):
    if is_running():
        print("GlucoBar is already running")
        return 0
    start_gui()
    return 0


def cmd_stop(_args):
    if not is_running():
        print("GlucoBar is not running")
        return 0
    if instance.request_quit():
        print("GlucoBar closed")
        return 0
    print("GlucoBar did not close: quit it from its menu", file=sys.stderr)
    return 1


def cmd_report(args):
    from .report import build_report, copy_to_clipboard
    cfg = load_config()
    i18n.set_language(cfg["language"])
    text = build_report(cfg, running=is_running())
    print(text)
    if not args.no_copy and copy_to_clipboard(text):
        print("\n" + t("cli_report_copied"))
    return 0


def cmd_forget(_args):
    forget_everything()
    print("Password, settings and log deleted.")
    return 0


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # accenti e frecce anche in cmd.exe
    parser = argparse.ArgumentParser(
        prog="glucobar",
        description="GlucoBar: your FreeStyle Libre or Dexcom glucose on the Windows desktop.",
        epilog="Settings: " + ", ".join(SETTINGS))
    parser.add_argument("--version", action="version", version=f"GlucoBar {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.add_parser("setup", help="interactive setup (arrow keys)").set_defaults(func=cmd_setup)
    sub.add_parser("status", help="show the current glucose reading").set_defaults(
        func=cmd_status)
    p = sub.add_parser("set", help="change settings: glucobar set unit=mmol/L low=80")
    p.add_argument("assignments", nargs="+", metavar="key=value")
    p.set_defaults(func=cmd_set)
    p = sub.add_parser("get", help="show settings")
    p.add_argument("keys", nargs="*", metavar="key")
    p.set_defaults(func=cmd_get)
    sub.add_parser("login", help="change sensor or account").set_defaults(func=cmd_login)
    sub.add_parser("start", help="start GlucoBar").set_defaults(func=cmd_start)
    sub.add_parser("stop", help="close GlucoBar").set_defaults(func=cmd_stop)
    sub.add_parser("forget", help="delete password and settings").set_defaults(func=cmd_forget)
    p = sub.add_parser("report", help="diagnostic report for bug reports (copied to clipboard)")
    p.add_argument("--no-copy", action="store_true", help="only print it")
    p.set_defaults(func=cmd_report)
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        print("\nStart with:  glucobar setup")
        return 0
    return args.func(args)

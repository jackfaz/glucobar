"""Finestra Promemoria (clic destro → Promemoria…): l'elenco, con un clic si aggiunge,
si modifica, si spegne o si cancella. La logica delle scadenze è in reminders.py."""

import time
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk

from . import reminders
from .config import save_config
from .i18n import t
from .ui_common import FONT

DIM = "#6b6f76"
SUGGESTIONS = ("rem_s_pickup", "rem_s_order", "rem_s_insulin", "rem_s_change", "rem_s_visit")


def day_names():
    return t("days_short").split(",")


def fmt_date(ts_or_day):
    day = ts_or_day if isinstance(ts_or_day, date) else date.fromtimestamp(ts_or_day)
    return day.strftime("%d/%m/%Y")


def fmt_when(ts):
    """"gio 29/10 08:00": il giorno della settimana aiuta a capire "quando"."""
    moment = datetime.fromtimestamp(ts)
    return f"{day_names()[moment.weekday()]} {moment:%d/%m %H:%M}"


def describe(rem):
    """Quando scatta, in parole: "Ogni giorno alle 08:00", "lun, gio alle 08:00"..."""
    kind, at = rem["kind"], rem["time"]
    if kind == "weekly":
        names = day_names()
        return t("rem_desc_weekly", days=", ".join(names[d] for d in sorted(rem["days"])), t=at)
    if kind == "interval":
        return t("rem_desc_interval", n=rem["every"], t=at,
                 d=fmt_date(date.fromisoformat(rem["date"])))
    if kind == "once":
        return t("rem_desc_once", d=fmt_date(date.fromisoformat(rem["date"])), t=at)
    if kind == "sensor":
        return t("rem_desc_sensor", n=rem.get("before", 0), t=at)
    return t("rem_desc_daily", t=at)


class RemindersWindow:
    current = None   # una finestra sola

    @classmethod
    def open(cls, ctl):
        if cls.current and cls.current.win.winfo_exists():
            cls.current.win.deiconify()
            cls.current.win.lift()
            cls.current.win.focus_force()
        else:
            cls.current = cls(ctl)

    def __init__(self, ctl):
        self.ctl = ctl
        self.cfg = ctl.cfg
        self.vars = []
        self.win = win = tk.Toplevel(ctl.root)
        win.title(t("rem_title"))
        win.resizable(False, False)
        win.protocol("WM_DELETE_WINDOW", self.close)
        win.bind("<Escape>", lambda _e: self.close())
        tk.Label(win, text=t("rem_intro"), font=(FONT, 10), justify="left", anchor="w",
                 wraplength=470).pack(fill="x", padx=16, pady=(14, 6))
        self.list = tk.Frame(win)
        self.list.pack(fill="x", padx=16)
        bottom = tk.Frame(win)
        bottom.pack(fill="x", padx=16, pady=(12, 14))
        tk.Button(bottom, text=t("rem_add"), font=(FONT, 9), command=self.add).pack(side="left")
        tk.Button(bottom, text=t("button_close"), width=10, command=self.close,
                  default="active").pack(side="right")
        self.refresh()
        win.update_idletasks()
        win.geometry(f"+{(win.winfo_screenwidth() - win.winfo_reqwidth()) // 2}"
                     f"+{max(0, (win.winfo_screenheight() - win.winfo_reqheight()) // 4)}")
        win.attributes("-topmost", True)
        win.focus_force()

    def items(self):
        return self.cfg.setdefault("reminders", [])

    def refresh(self):
        for child in self.list.winfo_children():
            child.destroy()
        self.vars = []
        if not self.items():
            tk.Label(self.list, text=t("rem_empty"), font=(FONT, 10), fg=DIM,
                     anchor="w").pack(fill="x", pady=8)
            return
        now = time.time()
        end = self.ctl.sensor_end()
        for rem in self.items():
            row = tk.Frame(self.list, bd=1, relief="groove", padx=8, pady=6)
            row.pack(fill="x", pady=3)
            on = tk.BooleanVar(master=self.win, value=rem.get("enabled", True))
            self.vars.append(on)
            tk.Checkbutton(row, variable=on, command=lambda r=rem, v=on: self.toggle(r, v.get())
                           ).grid(row=0, column=0, rowspan=2, sticky="n")
            tk.Label(row, text=rem["title"], font=(FONT, 10, "bold"), anchor="w",
                     wraplength=280, justify="left").grid(row=0, column=1, sticky="w")
            details = describe(rem)
            upcoming = reminders.next_time(rem, now, end)
            if rem["kind"] == "sensor" and not end:
                details += "\n" + t("rem_sensor_only")
            elif rem.get("enabled", True):
                details += "\n" + (t("rem_next", when=fmt_when(upcoming)) if upcoming
                                   else t("rem_none_next"))
            if rem.get("done_at"):
                details += "\n" + t("rem_last_done", when=fmt_when(rem["done_at"]))
            tk.Label(row, text=details, font=(FONT, 9), fg=DIM, anchor="w", justify="left",
                     wraplength=280).grid(row=1, column=1, sticky="w")
            buttons = tk.Frame(row)
            buttons.grid(row=0, column=2, rowspan=2, sticky="e")
            tk.Button(buttons, text=t("rem_edit"), font=(FONT, 9),
                      command=lambda r=rem: self.edit(r)).pack(side="left", padx=(0, 4))
            tk.Button(buttons, text=t("rem_delete"), font=(FONT, 9),
                      command=lambda r=rem: self.delete(r)).pack(side="left")
            row.columnconfigure(1, weight=1, minsize=300)

    def save(self):
        save_config(self.cfg)
        self.refresh()

    def toggle(self, rem, on):
        rem["enabled"] = on
        rem["snooze_until"] = None
        # riacceso: non deve tirar fuori subito una scadenza di prima
        rem["fired"] = max(rem.get("fired") or 0, time.time()) if on else rem.get("fired")
        self.save()

    def delete(self, rem):
        if messagebox.askyesno(t("rem_title"), t("rem_delete_confirm", title=rem["title"]),
                               parent=self.win):
            self.cfg["reminders"] = [r for r in self.items() if r["id"] != rem["id"]]
            self.save()

    def add(self):
        rem = Editor(self, None).result
        if rem:
            self.items().append(rem)
            self.save()

    def edit(self, rem):
        changed = Editor(self, rem).result
        if changed:
            rem.update(changed, fired=time.time(), snooze_until=None)
            self.save()

    def close(self):
        RemindersWindow.current = None
        self.win.destroy()


class Editor:
    """Aggiungere o modificare un promemoria. `result`: il promemoria, o None."""

    def __init__(self, parent, rem):
        self.result = None
        cfg = parent.cfg
        rem = rem or reminders.new("", "daily")
        today = date.today()
        self.dlg = dlg = tk.Toplevel(parent.win)
        dlg.title(t("rem_title"))
        dlg.resizable(False, False)
        pad = {"padx": 16}

        tk.Label(dlg, text=t("rem_what"), font=(FONT, 10, "bold")).pack(anchor="w", pady=(14, 2), **pad)
        self.title = ttk.Combobox(dlg, values=[t(k) for k in SUGGESTIONS], width=42, font=(FONT, 10))
        self.title.set(rem["title"])
        self.title.pack(anchor="w", **pad)

        tk.Label(dlg, text=t("rem_when"), font=(FONT, 10, "bold")).pack(anchor="w", pady=(12, 2), **pad)
        self.kind = tk.StringVar(master=dlg, value=rem["kind"])
        kinds = list(reminders.KINDS)
        self.rows = {}
        for kind in kinds:
            tk.Radiobutton(dlg, text=t(f"rem_kind_{kind}"), value=kind, variable=self.kind,
                           font=(FONT, 10), anchor="w", command=self.show_kind).pack(fill="x", **pad)
            row = tk.Frame(dlg)
            self.rows[kind] = row
            row.pack(fill="x", padx=(40, 16))

        # giorni della settimana
        self.days = []
        for i, name in enumerate(day_names()):
            v = tk.BooleanVar(master=dlg, value=i in (rem.get("days") or []))
            self.days.append(v)
            tk.Checkbutton(self.rows["weekly"], text=name, variable=v, font=(FONT, 9)).pack(side="left")
        # ogni N giorni, da una data
        start = date.fromisoformat(rem["date"]) if rem.get("date") else today
        tk.Label(self.rows["interval"], text=t("rem_every"), font=(FONT, 9)).pack(side="left")
        self.every = tk.Spinbox(self.rows["interval"], from_=1, to=365, width=4, font=(FONT, 9))
        self.every.delete(0, "end")
        self.every.insert(0, str(rem.get("every") or 7))
        self.every.pack(side="left", padx=4)
        tk.Label(self.rows["interval"], text=t("rem_days_from"), font=(FONT, 9)).pack(side="left")
        self.interval_date = self.date_fields(self.rows["interval"], start)
        # una volta
        tk.Label(self.rows["once"], text=t("rem_on"), font=(FONT, 9)).pack(side="left")
        self.once_date = self.date_fields(self.rows["once"], start)
        # prima della fine del sensore
        self.before = tk.Spinbox(self.rows["sensor"], from_=0, to=14, width=4, font=(FONT, 9))
        self.before.delete(0, "end")
        self.before.insert(0, str(rem.get("before", 3)))
        self.before.pack(side="left")
        tk.Label(self.rows["sensor"], text=t("rem_before"), font=(FONT, 9)).pack(side="left", padx=4)
        if cfg.get("source", "libre") != "libre":
            tk.Label(self.rows["sensor"], text=t("rem_sensor_only"), font=(FONT, 9), fg=DIM,
                     wraplength=380, justify="left").pack(side="left")

        row = tk.Frame(dlg)
        row.pack(anchor="w", pady=(12, 0), **pad)
        tk.Label(row, text=t("rem_at"), font=(FONT, 10, "bold")).pack(side="left")
        hours, minutes = rem["time"].split(":")
        self.hour = self.spin(row, 0, 23, int(hours), 1)
        tk.Label(row, text=":", font=(FONT, 10)).pack(side="left")
        self.minute = self.spin(row, 0, 59, int(minutes), 5)

        self.error = tk.Label(dlg, text="", fg="#c62828", font=(FONT, 9))
        self.error.pack(anchor="w", **pad)
        buttons = tk.Frame(dlg)
        buttons.pack(fill="x", padx=16, pady=(6, 14))
        tk.Button(buttons, text=t("button_cancel"), width=10, command=dlg.destroy).pack(side="right")
        tk.Button(buttons, text=t("rem_save"), width=10, command=self.ok, default="active").pack(
            side="right", padx=(0, 6))
        dlg.bind("<Return>", self.ok)
        dlg.bind("<Escape>", lambda _e: dlg.destroy())
        self.base = rem
        self.show_kind()
        dlg.update_idletasks()
        dlg.geometry(f"+{(dlg.winfo_screenwidth() - dlg.winfo_reqwidth()) // 2}"
                     f"+{max(0, (dlg.winfo_screenheight() - dlg.winfo_reqheight()) // 4)}")
        dlg.attributes("-topmost", True)
        dlg.focus_force()
        self.title.focus_set()
        dlg.grab_set()
        parent.win.wait_window(dlg)

    @staticmethod
    def spin(parent, low, high, value, step):
        box = tk.Spinbox(parent, from_=low, to=high, increment=step, width=3, font=(FONT, 10),
                         format="%02.0f", wrap=True)
        box.delete(0, "end")
        box.insert(0, f"{value:02d}")
        box.pack(side="left", padx=2)
        return box

    def date_fields(self, parent, day):
        """Giorno / mese / anno: tre caselle, più semplici di una data da scrivere."""
        fields = []
        for low, high, value, width in ((1, 31, day.day, 3), (1, 12, day.month, 3),
                                        (2024, 2100, day.year, 5)):
            box = tk.Spinbox(parent, from_=low, to=high, width=width, font=(FONT, 9))
            box.delete(0, "end")
            box.insert(0, str(value))
            box.pack(side="left", padx=1)
            fields.append(box)
            if len(fields) < 3:
                tk.Label(parent, text="/", font=(FONT, 9)).pack(side="left")
        return fields

    def show_kind(self):
        """Mostra le caselle della scelta fatta e disattiva le altre."""
        for kind, row in self.rows.items():
            state = "normal" if kind == self.kind.get() else "disabled"
            for child in row.winfo_children():
                try:
                    child.config(state=state)
                except tk.TclError:
                    pass

    @staticmethod
    def read_date(fields):
        day, month, year = (int(f.get()) for f in fields)
        return date(year, month, day).isoformat()

    def ok(self, _event=None):
        kind = self.kind.get()
        rem = {"title": self.title.get().strip(), "kind": kind}
        try:
            rem["time"] = f"{int(self.hour.get()):02d}:{int(self.minute.get()):02d}"
            if kind == "weekly":
                rem["days"] = [i for i, v in enumerate(self.days) if v.get()]
            elif kind == "interval":
                rem["every"] = int(self.every.get())
                rem["date"] = self.read_date(self.interval_date)
            elif kind == "once":
                rem["date"] = self.read_date(self.once_date)
            elif kind == "sensor":
                rem["before"] = int(self.before.get())
        except (TypeError, ValueError):
            self.error.config(text=t("rem_invalid"))
            return
        if not reminders.valid(dict(self.base, **rem)):
            self.error.config(text=t("rem_invalid"))
            return
        if self.base.get("title"):   # modifica: solo i campi cambiati
            self.result = rem
        else:
            at = rem.pop("time")
            self.result = reminders.new(at=at, **rem)
        self.dlg.destroy()

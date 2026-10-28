"""Un solo menu di GlucoBar, mostrato in tre modi: col clic destro sugli elementi
(Tkinter), sull'icona vicino all'orologio (pystray) e nella barra dei menu del Mac
(AppKit, vedi macbar.py). Il controller descrive le voci con `Item`; ogni menu le
ricostruisce quando si apre, così spunte e voci (es. "nuova versione") sono sempre
aggiornate."""

import tkinter as tk


class Item:
    """Una voce: comando (`action(*args)`), casella (`checked` True/False), scelta tra
    più valori (`radio`), sottomenu (`children`) o testo grigio (`enabled=False`)."""

    def __init__(self, label, action=None, *args, checked=None, radio=False, children=None,
                 default=False, enabled=True):
        self.label, self.action, self.args = label, action, args
        self.checked, self.radio, self.children = checked, radio, children
        self.default = default
        self.enabled = enabled and (action is not None or children is not None)


SEPARATOR = None


def radio_items(choices, current, action):
    """[(valore, testo)] -> voci a scelta singola che chiamano action(valore)."""
    return [Item(label, action, value, checked=value == current, radio=True)
            for value, label in choices]


def fill_tk(menu, items, post):
    """Riempie un tk.Menu (da chiamare in `postcommand`). I comandi passano da
    `post`, così vengono eseguiti a menu chiuso."""
    for child in list(menu.winfo_children()):
        child.destroy()   # i sottomenu della volta prima
    menu.delete(0, "end")
    keep = []
    for item in items:
        if item is SEPARATOR:
            menu.add_separator()
            continue
        if item.children is not None:
            sub = tk.Menu(menu, tearoff=0)
            fill_tk(sub, item.children, post)
            menu.add_cascade(label=item.label, menu=sub)
            continue
        options = {"label": item.label, "state": "normal" if item.enabled else "disabled"}
        if item.action is not None:
            options["command"] = _poster(post, item.action, item.args)
        if item.checked is None:
            menu.add_command(**options)
        else:
            var = tk.BooleanVar(master=menu, value=item.checked)
            keep.append(var)
            if item.radio:
                menu.add_radiobutton(variable=var, value=True, **options)
            else:
                menu.add_checkbutton(variable=var, **options)
    menu._vars = keep   # le variabili devono vivere quanto il menu


_open = 0   # menu col clic destro aperti adesso


def menu_open():
    """C'è un menu aperto? Allora gli elementi "sempre in primo piano" non devono tornare
    davanti: coprirebbero il menu (0.9.2, pannello in primo piano)."""
    return _open > 0


def popup(owner, items, post, x, y):
    """Apre il menu col clic destro: costruito adesso, da zero, e preparato del tutto
    prima di mostrarlo. Ricostruirlo dentro `postcommand`, mentre Windows lo sta già
    aprendo, lasciava i sottomenu con le voci vecchie: la prima scelta (es. "Aggiorna
    ogni → 10 s") non faceva niente e funzionava solo la seconda volta (0.8.4)."""
    old = getattr(owner, "_glucobar_menu", None)
    if old is not None:
        try:
            old.destroy()
        except tk.TclError:
            pass
    menu = tk.Menu(owner, tearoff=0)
    fill_tk(menu, items, post)
    owner._glucobar_menu = menu
    menu.update_idletasks()   # Tk prepara i menu di Windows (anche i sottomenu) adesso
    global _open
    _open += 1
    try:
        menu.tk_popup(x, y)   # su Windows resta qui finché il menu è aperto
    finally:
        _open -= 1
    return menu


def _poster(post, action, args):
    return lambda: post(action, *args)


def to_pystray(items, post):
    """Le stesse voci per pystray (icona vicino all'orologio, thread dell'icona)."""
    import pystray
    out = []
    for item in items:
        if item is SEPARATOR:
            out.append(pystray.Menu.SEPARATOR)
        elif item.children is not None:
            out.append(pystray.MenuItem(item.label,
                                        pystray.Menu(*to_pystray(item.children, post))))
        else:
            # pystray conta gli argomenti delle funzioni: niente lambda con default
            action = _poster(post, item.action, item.args) if item.action else None
            checked = None if item.checked is None else _const(item.checked)
            out.append(pystray.MenuItem(item.label, action, checked=checked, radio=item.radio,
                                        default=item.default, enabled=item.enabled))
    return out


def _const(value):
    return lambda _item: value

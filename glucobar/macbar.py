"""Il valore nella barra dei menu del Mac (in alto a destra, accanto all'orologio).

Prende il posto dell'icona di Windows: mostra valore e freccia colorati e, al clic,
il menu di GlucoBar. Usa AppKit (PyObjC) nello stesso ciclo di eventi di Tkinter:
tutto resta nel thread principale, e i comandi passano comunque da `ctl.post()` per
non lavorare dentro il menu mentre è aperto.
"""

import objc
from AppKit import (NSAttributedString, NSColor, NSFont, NSFontAttributeName,
                    NSForegroundColorAttributeName, NSMenu, NSMenuItem, NSStatusBar,
                    NSVariableStatusItemLength)
from Foundation import NSObject

from .i18n import t
from .menus import SEPARATOR
from .theme import palette, taskbar_light
from .ui_common import GREY, age_minutes, beside_value, fmt_value, is_stale

NS_ON, NS_OFF = 1, 0          # NSControlStateValueOn / Off
SEMIBOLD = 0.3                # NSFontWeightSemibold


def ns_color(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return NSColor.colorWithSRGBRed_green_blue_alpha_(r, g, b, 1.0)


class _Target(NSObject):
    """Riceve i clic delle voci (tag = posizione in `bar.actions`) e ricostruisce il
    menu ogni volta che si apre, così spunte e lingua sono sempre aggiornate."""

    def initWithBar_(self, bar):
        self = objc.super(_Target, self).init()
        if self is None:
            return None
        self.bar = bar
        return self

    def clicked_(self, sender):
        self.bar.clicked(sender.tag())

    def menuNeedsUpdate_(self, menu):
        self.bar.fill_menu(menu)


class MacMenuBar:
    def __init__(self, ctl):
        self.ctl = ctl
        self.ready = False
        self.item = None
        self.actions = []

    # ---- stessa interfaccia di tray.TrayIcon ----
    def start(self):
        self.item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength)
        self.target = _Target.alloc().initWithBar_(self)
        self.menu = NSMenu.alloc().init()
        self.menu.setAutoenablesItems_(False)
        self.menu.setDelegate_(self.target)
        self.item.setMenu_(self.menu)
        self.ready = True
        self.set_visible("tray" in self.ctl.cfg["elements"])
        self.render()

    def set_visible(self, visible):
        if self.item is not None:
            self.item.setVisible_(bool(visible))

    def update_menu(self):
        pass   # il menu si ricostruisce da solo ogni volta che si apre

    def show_hint(self):
        pass   # sul Mac il valore è sempre in vista nella barra dei menu

    def stop(self):
        if self.item is not None:
            NSStatusBar.systemStatusBar().removeStatusItem_(self.item)
            self.item = None

    def render(self):
        if self.item is None:
            return
        ctl, cfg, c = self.ctl, self.ctl.cfg, self.ctl.current
        if not c:
            text, color = "--", GREY
            tooltip = "GlucoBar: " + (ctl.error or t("connecting"))
        else:
            stale = is_stale(cfg, c)
            beside = beside_value(cfg, ctl.readings, c)
            text = fmt_value(cfg, c["mgdl"]) + (" " + beside if beside else "")
            pal = palette(cfg, light=taskbar_light())
            color = pal.stale if stale else pal.value(cfg, c["mgdl"])
            age = age_minutes(c)
            tooltip = f"{text} {cfg['unit']} · " + (t("now") if age == 0 else t("min_ago", n=age))
            if stale:
                tooltip += " · " + t("stale")
            if ctl.error:
                tooltip += f"\n⚠ {ctl.error}"
        font = NSFont.monospacedDigitSystemFontOfSize_weight_(NSFont.systemFontSize(), SEMIBOLD)
        title = NSAttributedString.alloc().initWithString_attributes_(
            text, {NSFontAttributeName: font, NSForegroundColorAttributeName: ns_color(color)})
        button = self.item.button()
        button.setAttributedTitle_(title)
        button.setToolTip_(tooltip)

    # ---- menu ----
    def clicked(self, index):
        if 0 <= index < len(self.actions):
            fn, args = self.actions[index]
            self.ctl.post(fn, *args)

    def _add(self, menu, title, fn=None, *args, checked=None):
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, None, "")
        if fn is not None:
            item.setTarget_(self.target)
            item.setAction_("clicked:")
            item.setTag_(len(self.actions))
            self.actions.append((fn, args))
        if checked is not None:
            item.setState_(NS_ON if checked else NS_OFF)
        menu.addItem_(item)
        return item

    def _submenu(self, menu, title):
        item = self._add(menu, title)
        sub = NSMenu.alloc().init()
        sub.setAutoenablesItems_(False)
        item.setSubmenu_(sub)
        return sub

    def fill_menu(self, menu):
        menu.removeAllItems()
        self.actions = []
        self._fill(menu, self.ctl.menu_items())

    def _fill(self, menu, items):
        for item in items:
            if item is SEPARATOR:
                menu.addItem_(NSMenuItem.separatorItem())
            elif item.children is not None:
                self._fill(self._submenu(menu, item.label), item.children)
            else:
                ns_item = self._add(menu, item.label, item.action, *item.args,
                                    checked=item.checked)
                ns_item.setEnabled_(item.enabled)

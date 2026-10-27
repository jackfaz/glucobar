<p align="center"><img src="docs/banner.png" alt="GlucoBar: your FreeStyle Libre glucose on the Windows taskbar"></p>

<p align="center">
  <a href="https://github.com/jackfaz/glucobar/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/jackfaz/glucobar?include_prereleases&label=release&color=3ecf6e"></a>
  <a href="https://github.com/jackfaz/glucobar/releases"><img alt="Downloads" src="https://img.shields.io/github/downloads/jackfaz/glucobar/total?color=3ecf6e"></a>
  <a href="https://github.com/jackfaz/glucobar/actions/workflows/build.yml"><img alt="Build" src="https://img.shields.io/github/actions/workflow/status/jackfaz/glucobar/build.yml?branch=main"></a>
  <img alt="Windows 10/11" src="https://img.shields.io/badge/Windows-10%20%7C%2011-0078d4">
  <img alt="6 languages" src="https://img.shields.io/badge/languages-6-f5a524">
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-lightgrey"></a>
</p>

<p align="center">
  <a href="https://github.com/jackfaz/glucobar/releases/latest"><b>⬇️ Download for Windows</b></a> ·
  <a href="#install">Install</a> ·
  <a href="#use">Use</a> ·
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="README.it.md">🇮🇹 Italiano</a>
</p>

GlucoBar reads your latest sensor value from **LibreLinkUp** (Abbott's sharing service)
and shows it on your PC, colour-coded, with the trend arrow and how many minutes ago it
was measured.

- 🩸 **Always in sight** — on the taskbar next to the clock, in a small window, in a panel on
  your desktop or as a number icon. Pick any combination.
- 📈 **Details when you want them** — chart up to 12 hours, average, min, max, time in range,
  15-minute change, sensor day.
- 🖥️ **Second monitor** and **full-screen aware** — hides during videos and games.
- 🔒 **Private** — password encrypted in Windows Credential Manager, data sent only to Abbott.
- 🌍 **6 languages** — English, Italiano, Español, Français, Deutsch, Português.
- 🆓 **Free and open source** (MIT), no administrator rights needed.

Choose what to show — **any combination** — during installation, and change it any time by
right-clicking any GlucoBar element (*Show* menu): unit, language, account and quit are there too.

| On the taskbar (recommended) | Small window |
|---|---|
| ![Taskbar](docs/preview_taskbar.png) | ![Window](docs/preview_window.png) |
| Value, arrow and minutes next to the clock. Works on a second monitor too; hides during full-screen videos. | Small always-on-top window with a 3-hour chart. Drag it anywhere. |
| **Desktop panel** | **Icon next to the clock** |
| ![Desktop panel](docs/preview_desktop.png) | ![Icon next to the clock](docs/preview_tray.png) |
| Panel on the desktop, behind your windows: large chart (3, 6 or 12 hours), average, min, max, time in range, 15-minute change and sensor day. Move it and resize it from the bottom-right corner. | The coloured number in an icon next to the clock; hover it for arrow and minutes. Optional: untick it if you don't want it. |

Green = in range (70–180 mg/dL) · Orange = above 180 · Red = below 70 or above 250 ·
Grey = reading older than 15 minutes.

Languages: English, Italiano, Español, Français, Deutsch, Português.

> ⚠️ **GlucoBar is not a medical device.** Do not use it to decide insulin doses or to treat
> a hypo — always rely on your reader or the official app. It uses an **unofficial API** that
> Abbott can change at any time.

## Install

1. **Set up LibreLinkUp (once).** In the **LibreLink** app on your phone: *Share → Connected
   apps → LibreLinkUp → Add*, and invite an email address (preferably a different one from
   your LibreLink account). Install the **LibreLinkUp** app, sign in with that email, accept
   the invitation and the terms of use. You can uninstall LibreLinkUp afterwards.
2. Download `GlucoBar-Setup-x.y.z.exe` from the [Releases](../../releases/latest) page and run
   it. No administrator rights needed.
3. Choose the setup language, tick what to show (with previews) and whether to start GlucoBar
   with Windows.
4. On first start, enter the **LibreLinkUp** email and password.

Windows may show *"Windows protected your PC"* because the installer is not code-signed yet:
click *More info → Run anyway*.

## Use

- **Right-click any GlucoBar element** (the icon, the value on the taskbar, the window or the
  panel): refresh, *Show* (tick the elements you want), unit, language, change account, quit.
  **Double-click**: refresh now.
- Windows 11 hides new icons under the **^** arrow: drag the GlucoBar icon onto the taskbar to
  keep it visible.
- Taskbar mode on a second monitor: enable *Settings → Personalization → Taskbar → Taskbar
  behaviors → Show my taskbar on all displays*, then right-click the value → *Move to the other
  monitor*.
- Desktop panel: drag to move, drag the bottom-right corner to resize, right-click for the
  chart period and to lock it in place.

## Terminal

The installer adds the `glucobar` command to every new terminal:

```text
glucobar setup                 interactive setup: ↑/↓ to choose, Space to tick, Enter to confirm
glucobar status                current reading, e.g. "133 ↘ mg/dL · 2 min ago"
glucobar set unit=mmol/L low=80
glucobar set elements=desktop,tray autostart=true
glucobar get                   all settings
glucobar login                 change LibreLinkUp account
glucobar start | forget        start GlucoBar | delete password and settings
```

If GlucoBar is running, it applies the new settings within two seconds.

Silent install with your choices (handy for scripts and winget):

```text
GlucoBar-Setup-0.5.0.exe /VERYSILENT /ELEMENTS=taskbar,tray /LANG=en
```

## Settings

`%APPDATA%\GlucoBar\config.json`:

| Key | Default | Meaning |
|---|---|---|
| `elements` | `["taskbar", "tray"]` | What to show, any combination of `taskbar`, `tray` (icon next to the clock), `window`, `desktop` |
| `low` / `high` / `very_high` | 70 / 180 / 250 | Thresholds in mg/dL |
| `unit` | `mg/dL` | or `mmol/L` |
| `stale_minutes` | 15 | After this, the value turns grey |
| `refresh_seconds` | 60 | How often to fetch |
| `language` | `auto` | `en`, `it`, `es`, `fr`, `de`, `pt` |
| `taskbar_monitor` | 1 | 1 = main monitor, 2 = second, … |
| `taskbar_offset` | 0 | Extra pixels (negative = left) |
| `taskbar_bg` | auto | Your taskbar colour, e.g. `#202020`, if you see a halo around the digits |
| `taskbar_transparent` | true | `false` for a solid background |
| `desktop_hours` | 12 | Desktop panel chart period: 3, 6 or 12 |
| `desktop_alpha` | 0.92 | Desktop panel opacity (1 = solid) |

Log file: `%APPDATA%\GlucoBar\glucobar.log`.

## Privacy

- Your password is stored **encrypted in Windows Credential Manager** (entry
  `GlucoBar:LibreLinkUp`), never in the settings file.
- GlucoBar talks **only to Abbott's LibreView servers**. No analytics, no other servers.
- Uninstalling asks whether to delete settings and the saved password too (also the first version's
  `.glicemia_widget.json`). You can do the same any time with `GlucoBar.exe --forget`.

## Why "on" and not "inside" the taskbar?

On Windows 11 25H2 a window embedded in the taskbar (`SetParent` on `Shell_TrayWnd`, the
technique used by TrafficMonitor) is drawn *underneath* the taskbar's acrylic background and
is invisible. GlucoBar instead keeps a transparent, borderless, always-on-top window exactly
over the taskbar and re-asserts it every 500 ms.

## Build from source

```bat
pip install -r requirements.txt pyinstaller
python -m unittest discover -s tests
python run_glucobar.py --mode desktop          :: run without building
pyinstaller --noconfirm --clean glucobar.spec
python tools\previews_to_bmp.py
iscc /DAppVersion=0.5.0 installer\glucobar.iss    :: needs Inno Setup 6
```

Releases are built by GitHub Actions (`.github/workflows/build.yml`): push a tag like
`v0.5.0` and the installer is attached to a new release. The mode previews are made with
`tools/compose_previews.py`.

## Credits and trademarks

GlucoBar is an independent open-source project, not affiliated with or endorsed by Abbott.
FreeStyle, Libre, LibreLink and LibreLinkUp are trademarks of Abbott. The LibreLinkUp API
details come from the work of the open-source diabetes community.

License: [MIT](LICENSE).

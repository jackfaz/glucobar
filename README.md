<p align="center"><img src="docs/banner.png" alt="GlucoBar: your Libre or Dexcom glucose on the Windows taskbar"></p>

<p align="center">
  <a href="https://github.com/jackfaz/glucobar/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/jackfaz/glucobar?include_prereleases&label=release&color=3ecf6e"></a>
  <a href="https://github.com/jackfaz/glucobar/releases"><img alt="Downloads" src="https://img.shields.io/github/downloads/jackfaz/glucobar/total?color=3ecf6e"></a>
  <a href="https://github.com/jackfaz/glucobar/actions/workflows/build.yml"><img alt="Build" src="https://img.shields.io/github/actions/workflow/status/jackfaz/glucobar/build.yml?branch=main"></a>
  <img alt="Windows 10/11" src="https://img.shields.io/badge/Windows-10%20%7C%2011-0078d4">
  <img alt="6 languages" src="https://img.shields.io/badge/languages-6-f5a524">
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-lightgrey"></a>
</p>

<p align="center">
  <a href="https://github.com/jackfaz/glucobar/releases/latest"><b>Download for Windows</b></a> ·
  <a href="#install">Install</a> ·
  <a href="#mac-beta">Mac</a> ·
  <a href="#setting-up-librelinkup">LibreLinkUp setup</a> ·
  <a href="#use">Use</a> ·
  <a href="#sensors">Sensors</a> ·
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="README.it.md">Italiano</a>
</p>

GlucoBar shows your FreeStyle Libre or Dexcom reading on your Windows PC, so you can keep an
eye on it while you work without reaching for your phone. It reads the latest value from
LibreLinkUp (Abbott's sharing service) or Dexcom Share, and shows it with the trend arrow and
how long ago it was measured. Nightscout and Nocturne sites work too, and there is a
[Mac version](#mac-beta) in beta.

You can show it in four places, alone or together: on the taskbar next to the clock, as an
icon in the notification area, in a small window that stays on top, or in a larger panel on
the desktop with a 12-hour chart and a few statistics. It works on a second monitor too, and
hides while a video or a game is full screen.

Your password stays encrypted in Windows Credential Manager and is only sent to your sensor
maker's servers. GlucoBar is free, open source (MIT), and available in English, Italian, Spanish,
French, German and Portuguese.

| On the taskbar | Small window |
|---|---|
| ![Taskbar](docs/preview_taskbar.png) | ![Window](docs/preview_window.png) |
| Value, arrow and minutes next to the clock. | Always on top, with a 3-hour chart. Drag it anywhere. |
| **Desktop panel** | **Icon next to the clock** |
| ![Desktop panel](docs/preview_desktop.png) | ![Icon next to the clock](docs/preview_tray.png) |
| Behind your windows: chart of the last 3, 6 or 12 hours, average, min, max, time in range, 15-minute change and sensor day. Resizable. | The coloured number in the notification area. Hover it for the arrow and the minutes. |

Colours: green in range (70–180 mg/dL), orange above 180, red below 70 or above 250, grey when
the reading is more than 15 minutes old. Thresholds can be changed.

> **GlucoBar is not a medical device.** Do not use it to decide insulin doses or to treat a
> hypo: always rely on your reader or the official app. It uses an unofficial API that Abbott
> can change at any time.

## Sensors

| Sensor | Read through | Status |
|---|---|---|
| FreeStyle Libre (Libre 2, Libre 3 and their Plus versions) | LibreLinkUp | Supported |
| Dexcom G6, G7, ONE+ | Dexcom Share | Beta, testers wanted |
| Any sensor uploading to Nightscout or Nocturne (Medtronic, Eversense, xDrip+, Juggluco, AndroidAPS, Loop, …) | Nightscout API | Beta, testers wanted |
| Medtronic Guardian / Simplera | CareLink | Being evaluated |

Dexcom and Nightscout support is new and has only been tested against simulated servers so
far. If you use them, please tell us in [Discussions](../../discussions) or in an
[issue](../../issues) whether it works for you.

Would you like another sensor? [Open an issue](../../issues) and tell us which one.

## Install

1. **Turn on sharing on your phone (once).**
   - **FreeStyle Libre:** share your readings with LibreLinkUp, using your own LibreLink
     account. It takes five minutes: see [Setting up LibreLinkUp](#setting-up-librelinkup).
   - **Dexcom:** in the **Dexcom** app, turn on **Share** and invite at least one follower.
     GlucoBar signs in with your own Dexcom account, not the follower's.
   - **Nightscout or Nocturne:** you need a site that already receives your readings. If it
     is not public, create a read-only token. Nightscout: *Admin Tools → Add new Subject*, role
     **readable**, and copy its token. Nocturne: *Settings → Connectors → API tokens → Create
     API token*, with read permission for **Blood glucose**.
2. Download the installer from the [Releases](../../releases/latest) page, or directly with
   this link, which always gives the latest version:
   https://github.com/jackfaz/glucobar/releases/latest/download/GlucoBar-Setup.exe.
   No administrator rights needed.
3. Choose the setup language, tick what to show (with previews) and whether to start GlucoBar
   with Windows.
4. On first start, choose your sensor and enter the account: the **LibreLinkUp** email for
   FreeStyle Libre (the same as LibreLink, if you followed the guide below), or your
   **Dexcom** email, phone number (with country code) or user name, or your **Nightscout** or
   **Nocturne** site address (the one you open in the browser) and token.

Windows may show *"Windows protected your PC"* because the installer is not code-signed yet:
click *More info → Run anyway*. Each release lists the installer's SHA-256 and a link to its
VirusTotal scan, so you can check the file before running it.

## Mac (beta)

On the Mac the value sits in the **menu bar**, next to the clock; click it for the GlucoBar
menu. The small window and the desktop panel work as on Windows. It needs a Mac with Apple
silicon (M1 or newer) and macOS 11 or later.

1. Download `GlucoBar-mac.dmg`:
   https://github.com/jackfaz/glucobar/releases/latest/download/GlucoBar-mac.dmg
2. Open it and drag **GlucoBar** onto **Applications**.
3. Open GlucoBar from Applications. The app is not notarized by Apple yet, so the first time
   macOS blocks it: open **System Settings → Privacy & Security**, scroll down to the message
   about GlucoBar and click **Open Anyway** (on macOS 14 and earlier you can also Control-click
   the app → **Open**). You only need to do this once.
4. Choose your sensor and enter the account, as on Windows.

From the menu you can also turn on **Open at login**. Passwords are kept in the macOS
**Keychain** (entries `GlucoBar:LibreLinkUp`, `GlucoBar:Dexcom`, `GlucoBar:Nightscout`) and the
settings in `~/Library/Application Support/GlucoBar/config.json`.

The `glucobar` command is inside the app. To use it from any terminal:

```text
sudo mkdir -p /usr/local/bin
sudo ln -sf /Applications/GlucoBar.app/Contents/MacOS/glucobar-cli /usr/local/bin/glucobar
```

To uninstall: turn off *Open at login*, quit GlucoBar, run `glucobar forget` if you want to
delete passwords and settings, and move GlucoBar to the Trash.

## Setting up LibreLinkUp

GlucoBar reads your FreeStyle Libre through LibreLinkUp, Abbott's app for sharing readings
with family and carers. You set it up once, on your phone, in a few minutes. The simplest way
is to share with yourself, using the account you already have in the LibreLink app.

![The steps in the LibreLink and LibreLinkUp apps](docs/librelinkup-setup.png)
<sub>Screenshots from the Italian version of the apps.</sub>

1. In the **LibreLink** app (the one that reads your sensor), open the menu and tap
   **Connected Apps**.
2. Next to **LibreLinkUp**, tap **Manage**.
3. Tap **Add Connection**, enter your name and **the email of your LibreLink account**, and
   send the invitation.
4. Install the **LibreLinkUp** app from the App Store or Google Play, tap **Log In** and use
   the **same email and password** as LibreLink (LibreLinkUp calls it your LibreView
   account). Accept the invitation and the terms of use: your reading appears in LibreLinkUp.
5. In GlucoBar, choose *FreeStyle Libre* and enter the same email and password.

After that you can uninstall LibreLinkUp from the phone. GlucoBar will tell you if you ever
need it again, for example when Abbott updates its terms of use.

You can also invite a different email, for example a family member's, and use that account
in GlucoBar instead: it works the same way.

**If GlucoBar shows an error**

| Message | What to do |
|---|---|
| *Wrong email or password* | Check that you can sign in to the LibreLinkUp app with the same email and password. |
| *No patient linked* | The invitation has not been accepted yet: open LibreLinkUp and accept it, or send it again from LibreLink. |
| *Open the LibreLinkUp app on your phone and accept the terms of use* | Open LibreLinkUp, accept, then right-click GlucoBar → *Refresh now*. |
| The value stays grey | No new reading for 15 minutes: check that the phone is near the sensor and online. |

## Use

- **Right-click any GlucoBar element** (the icon, the value on the taskbar, the window or the
  panel): refresh, *Show* (tick the elements you want), *Sensor*, *Settings…*, quit.
  **Double-click**: refresh now.
- **Settings…** has everything else, in tabs: *General* (account, language, unit, how often
  to update, start with Windows), *Values and alerts* (thresholds, alerts, delta),
  *Appearance* (theme and every colour), *Elements* (what to show, taskbar value, desktop
  panel) and *Updates* (installed version, *Check for updates now*, automatic updates).
- Windows 11 hides new icons under the **^** arrow: drag the GlucoBar icon onto the taskbar to
  keep it visible.
- Taskbar mode on a second monitor: enable *Settings → Personalization → Taskbar → Taskbar
  behaviors → Show my taskbar on all displays*, then right-click the value → *Move to the other
  monitor*.
- Desktop panel and small window: drag to move, drag the bottom-right corner to resize. On
  the panel, right-click for the chart period, to lock it in place, or to keep it *Always
  on top* of other windows (it hides while an app is full screen).
- Value on the taskbar: keep the mouse on it for a second to see the full chart just above
  it. Right-click → *Size* to make it smaller or larger. *Settings → Values and alerts →
  Show the change (delta)* adds the change since the previous reading (e.g. "3 min +5").
- *Settings…*: theme (light, dark or automatic, following Windows or macOS), every colour
  (the value in range, high, very high, low and old; backgrounds, text, chart and grid of the
  small window and the panel, for each theme; the background of the value on the taskbar)
  and thresholds. Changes show right away on every element.
- *Alerts* (off by default): a message when glucose is low, very high, or when no new data
  has arrived for a while. They come from the sensor's online service, a few minutes late,
  and only while the computer is on: **they do not replace your sensor's alarms**.
- *Sensor*: with LibreLinkUp, the day of use and the serial number (click to copy it), a
  reminder 24 hours and 2 hours before the end, and a message if the sensor seems to have
  stopped early or was replaced early. *Request a sensor replacement…* opens the
  manufacturer's page for your country and copies the serial number, ready to paste into
  the form.
- *Person*: if your LibreLinkUp account follows more than one person, choose who to show.
- When a new version is out, GlucoBar tells you and the first menu item installs it: on
  Windows it downloads the installer, checks its SHA-256 fingerprint and installs it in
  silence, then reopens with the same settings. Tick *Install new versions automatically* to
  skip the question. On the Mac it opens the download page.

## Terminal

The installer adds the `glucobar` command to every new terminal:

```text
glucobar setup                 interactive setup: ↑/↓ to choose, Space to tick, Enter to confirm
glucobar status                current reading, e.g. "133 ↘ mg/dL · 2 min ago"
glucobar set unit=mmol/L low=80
glucobar set elements=desktop,tray autostart=true
glucobar get                   all settings
glucobar login                 change sensor or account
glucobar start | stop          start GlucoBar | close it
glucobar forget                delete passwords, tokens and settings
glucobar report                diagnostic summary for bug reports, copied to the clipboard
```

If GlucoBar is running, it applies the new settings within two seconds.

Silent install with your choices (handy for scripts and winget):

```text
GlucoBar-Setup-0.9.3.exe /VERYSILENT /ELEMENTS=taskbar,tray /SENSOR=libre /LANG=en
```

## Settings

`%APPDATA%\GlucoBar\config.json`:

| Key | Default | Meaning |
|---|---|---|
| `source` | `libre` | `libre` (LibreLinkUp), `dexcom` (Dexcom Share) or `nightscout` |
| `dexcom_region` | `ous` | Where the Dexcom account was created: `ous` (outside the US), `us`, `jp` |
| `elements` | `["taskbar", "tray"]` | What to show, any combination of `taskbar`, `tray` (icon next to the clock), `window`, `desktop` |
| `low` / `high` / `very_high` | 70 / 180 / 250 | Thresholds in mg/dL |
| `unit` | `mg/dL` | or `mmol/L` |
| `stale_minutes` | 15 | After this, the value turns grey |
| `hover_chart` | true | Show the full chart when the mouse rests on the value on the taskbar |
| `show_delta` | false | Show the change since the previous reading, per 5 minutes, on the taskbar and the small window |
| `refresh_seconds` | 60 | How often to fetch, from 10 to 3600 seconds (also in Settings → General) |
| `language` | `auto` | `en`, `it`, `es`, `fr`, `de`, `pt` |
| `taskbar_monitor` | 1 | 1 = main monitor, 2 = second, … |
| `taskbar_offset` | 0 | Extra pixels (negative = left) |
| `taskbar_bg` | auto | Your taskbar colour, e.g. `#202020`, if you see a halo around the digits |
| `taskbar_transparent` | true | `false` for a solid background |
| `taskbar_scale` | 1.0 | Size of the value on the taskbar, 0.85–1.25 (also from the right-click menu → *Size*) |
| `window_scale` | 1.0 | Size of the small window, 0.8–2.5 (also by dragging its bottom-right corner) |
| `desktop_hours` | 12 | Desktop panel chart period: 3, 6 or 12 |
| `desktop_alpha` | 0.92 | Desktop panel opacity (1 = solid) |
| `desktop_on_top` | false | Keep the desktop panel above other windows (hidden while an app is full screen) |
| `theme` | `auto` | `auto` (follows Windows or macOS), `dark` or `light` |
| `palette` | `standard` | `standard` or `colorblind` |
| `color_in_range` / `color_high` / `color_very_high` / `color_low` / `color_stale` | auto | Your own colour for the value, e.g. `#00c060`; `auto` = the palette's |
| `taskbar_text` | auto | Colour of the minutes under the value on the taskbar |
| `alert_low` / `alert_high` / `alert_stale` | false | Alerts for low (below `low`), very high (above `very_high`) and no data (`stale_minutes`) |
| `update_check` | true | Check once a day whether a new version is out |
| `auto_update` | false | Windows: install new versions without asking |
| `sensor_life_days` | 14 | LibreLinkUp: how long your sensor lasts, for the end reminders (15 for Plus sensors) |

Log file: `%APPDATA%\GlucoBar\glucobar.log`.

## Privacy

- Your password is stored **encrypted in Windows Credential Manager** (entries
  `GlucoBar:LibreLinkUp`, `GlucoBar:Dexcom`, and `GlucoBar:Nightscout` for the token), never
  in the settings file.
- GlucoBar talks **only to the servers of your sensor's maker** (Abbott's LibreView or Dexcom
  Share) **or to your own Nightscout site**. No analytics.
- Once a day it asks GitHub which is the latest GlucoBar version (a public request that sends
  no data about you or your readings), and downloads the installer from GitHub only when you
  install an update. Turn it off from the menu or with `glucobar set update_check=false`.
- *Request a sensor replacement…* only opens the manufacturer's page in your browser and
  copies the serial number to your clipboard: GlucoBar sends nothing itself.
- Uninstalling asks whether to delete settings and the saved password too (also the first version's
  `.glicemia_widget.json`). You can do the same any time with `GlucoBar.exe --forget`.

## Code signing policy

The installer is not code-signed yet. We plan to apply to the
[SignPath Foundation](https://signpath.org) program for free code signing of open-source
projects once GlucoBar is more widely used.

- Committers and reviewers: [jackfaz](https://github.com/jackfaz)
- Approvers: [jackfaz](https://github.com/jackfaz)

Only installers built by GitHub Actions from this repository are signed.

This program will not transfer any information to other networked systems unless
specifically requested by the user or the person installing or operating it. The only
connections GlucoBar makes are to the servers of the user's sensor maker (Abbott LibreView
or Dexcom Share) or to the user's own Nightscout site, with the account the user enters, and
a daily check of the latest version on GitHub that the user can turn off.

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
iscc /DAppVersion=0.9.3 installer\glucobar.iss    :: needs Inno Setup 6
```

Releases are built by GitHub Actions (`.github/workflows/build.yml`): in *Actions → Build installer →
Run workflow*, tick *release* to publish the version written in `glucobar/__init__.py`
(pushing a tag like `v0.9.3` works too). The mode previews are made with
`tools/compose_previews.py`.

Each build also installs the previous release, opens it and installs the new version over it
in silence (as winget does), checking that settings, password and choices stay. Two more
workflows run on their own:

- *Live check* (daily): reads a value from the real LibreLinkUp, Dexcom Share and Nightscout
  with the accounts saved as repository secrets (`LIBRE_EMAIL`, `LIBRE_PASSWORD`,
  `DEXCOM_USER`, `DEXCOM_PASSWORD`, `DEXCOM_REGION`, `NIGHTSCOUT_URL`, `NIGHTSCOUT_TOKEN`; each
  service is skipped if its secrets are missing). The log only says "ok" or the error.
- *Soak test* (weekly, or by hand with a duration): keeps GlucoBar open with a reading every
  10 seconds and theme changes, and fails if memory, handles or graphics objects keep growing.

## Credits and trademarks

GlucoBar is an independent open-source project, not affiliated with or endorsed by Abbott
or Dexcom. FreeStyle, Libre, LibreLink and LibreLinkUp are trademarks of Abbott; Dexcom is a
trademark of Dexcom, Inc. The LibreLinkUp and Dexcom Share API details come from the work of
the open-source diabetes community (Nightscout, pydexcom and others). Nightscout is an
open-source project by the Nightscout Foundation; GlucoBar uses its documented API.

GlucoBar is free and will stay free. If it is useful to you and you want to support it, you
can [donate via PayPal](https://paypal.me/giacomofazioli).

License: [MIT](LICENSE).

# Changelog

All notable changes to GlucoBar are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
uses [Semantic Versioning](https://semver.org/).

## [0.11.2] - 2026-10-29

### Changed
- **Sounds wait for Apply**: in *Settings → Alerts and sounds* the sound, pack, repeat and
  volume you pick are only tried (▶, or right away when you pick one) until you press
  *Apply*, so you can listen to them all without changing anything. Closing the window with
  changes not applied asks whether to apply them.
- **Trend estimate on the chart**: the next 30 minutes have their own shaded zone on the right,
  labelled *estimate*, instead of a thin strip squeezed against the edge of a 12-hour chart.

### Fixed
- Changing two sounds one after the other could close GlucoBar. MP3 and M4A files are now
  converted by a separate GlucoBar process, so a problem in Windows' decoder can no longer
  close the app, and the window doesn't freeze while a long file is converted.

## [0.11.1] - 2026-10-29

### Fixed
- The Mac version of 0.11.0 was not built (a test stopped the build), so the Mac download
  stayed on 0.10.1. 0.11.1 brings the new alert sounds to the Mac too. On a Mac without a
  working sound player, alerts fall back to the system beep. Nothing changes on Windows.

## [0.11.0] - 2026-10-29

### Added
- **A sound for each alert, and your own sounds**: low, very high and no data each have
  their own sound. GlucoBar has seven of its own (falling beeps for low and rising beeps for
  very high by default, so you can tell them apart without looking), and any WAV, MP3 or M4A
  file works too: *Browse…* next to each alert. On Windows the files are converted once with
  Windows' own decoder, so nothing extra is installed.
- **Sound packs**: a folder of sounds, or a `.zip` brought in with *Import…*, becomes a pack
  you pick from a list; GlucoBar chooses the sound for each alert from the file names, or from
  an optional `pack.json`. All the sounds of every pack can also be mixed one by one.
- **Repeat low and very high separately**: e.g. low every 15 seconds and very high every
  minute, each until the value is back in range. A long sound stops as soon as you are back
  in range or press *Silence*.
- **Volume** slider for the alert sounds (only GlucoBar's, not the rest of the computer).
- **Alerts in the right-click menu**: *Alerts* turns each alert on or off and changes the
  pack, the sound and the repeat interval without opening Settings, and has *Silence*.
  (Thanks to the Reddit user who asked for all of this.)

### Changed
- Settings: alerts and sounds have their own tab, *Alerts and sounds*; the former *Values
  and alerts* tab is now *Values*. If you had *Repeat the sound* on in 0.10.1, both alerts
  keep repeating at the interval you chose.

## [0.10.1] - 2026-10-29

### Added
- **Alert sound, repeated if you want**: alerts now play a short alarm sound, and with
  *Repeat the sound every …* (*Settings → Values and alerts*) it plays again every 15 seconds,
  or up to 5 minutes, while the value stays low or very high, until it is back in range or
  you press *Silence* on the message (thanks for the suggestion on Reddit). *Test* plays it.

### Fixed
- Resizing the small window from its corner also moved it with the mouse: the drag reached
  the window around the corner too. Now it only grows or shrinks. The Windows test drags the
  corner with the mouse and checks that the window stays where it is.

## [0.10.0] - 2026-10-29

### Added
- **Reminders**: a Reminders window (right-click → *Reminders…*) for things like picking up
  medicines, ordering sensors or long-acting insulin: every day, on some days of the week,
  every few days, once, or a few days before the FreeStyle Libre sensor ends. The message
  has *Done* and *In 15 / 60 min*. No doses, ever.
- **Several people at once**: with LibreLinkUp, *Person → Also show …* puts other people
  followed with the same account next to the main one on the taskbar, and alerts say whose
  they are. A **nickname** for each person (*Settings → General → People*) appears next to
  the value, with any sensor.
- **Trend estimate (experimental)**, off by default: on the desktop panel and the hover
  chart, where the value would go in the next 30 minutes if it kept its recent trend, with a
  widening band, and an optional alert when the estimate goes below the low threshold. It
  shows a disclaimer to accept before turning on: it is not a forecast and not a medical
  device.
- **Connect other devices** (*Settings → Connections*, off by default): a local web address
  with the value as JSON, Nightscout-compatible addresses so displays made for Nightscout
  work with GlucoBar, and an OBS overlay page; and MQTT publishing with Home Assistant
  discovery. Local to this computer unless opened to the home network, optional access key.

## [0.9.8] - 2026-10-28

### Fixed
- The right-click menu of the icon next to the clock only ran *Quit*: its submenus did not
  open. GlucoBar rebuilt that menu at every reading and every 15 seconds, from another
  thread, and the old one was destroyed even while it was open. The menu is now built when
  you right-click the icon (thanks for the report on Reddit). A new test on Windows opens
  it and chooses *Show → Small window* after 0.5, 5, 12 and 20 seconds, with readings
  arriving every 10 seconds.

## [0.9.7] - 2026-10-28

### Added
- **Delta next to the value**: *Settings → Values and alerts → Next to the value* shows the
  change since the previous reading in place of the trend arrow ("142 +5"), or both
  ("142 ↗ +5"), on the taskbar, the small window, the desktop panel, the icon's tooltip and
  the Mac menu bar (thanks for the suggestion on Reddit). From the terminal:
  `glucobar set trend_style=delta`. The arrow stays until there is a previous reading to
  compare with.

### Fixed
- Includes the fix from 0.9.6, which was held back as a pre-release: with an auto-hidden
  taskbar, the right-click menu of the value only ran *Quit*.

## [0.9.6] - 2026-10-28

### Fixed
- With the taskbar set to hide automatically, the right-click menu of the value on the
  taskbar only ran *Quit*. While you moved to the other entries the taskbar slid down,
  GlucoBar hid the value and the menu closed with it. The value now waits until the menu is
  closed (thanks for the report on Reddit). The edges test chooses from that menu slowly, with
  the taskbar hidden, on Windows 10 and 11.

## [0.9.5] - 2026-10-28

### Added
- **Desktop panel over full-screen apps**: with *Always on top* on, *Also over full-screen
  apps* keeps the panel visible over a video or a full-screen app, like picture-in-picture
  (thanks for the suggestion on Reddit). Off by default (`desktop_over_fullscreen`).
- **Panel opacity** slider in *Settings → Elements*, applied while you drag it.

### Fixed
- With the desktop panel always on top, its right-click menu ended up behind the panel
  after a second. Elements that stay on top now wait while a menu is open.
- The first choice in a right-click submenu could be lost, for example *Show → Small window*
  in the small window's own menu needed two clicks. A right-click opened two menus in a row
  (one for the text, one for the window around it), and the second closed the first before
  Windows ran the choice. Now a right-click opens one menu.
- The build checks all three on Windows with the mouse, and the same tests fail on 0.9.4.

## [0.9.4] - 2026-10-28

### Fixed
- **Taskbar on the left, right or top** (Windows 10): the value now sits on the taskbar
  wherever it is. On a vertical taskbar it is as wide as the taskbar, just above the clock
  (or below Start with *Move left / right*), and the chart on hover opens beside it. Before,
  it stayed at the bottom of the screen, or even off screen (thanks for the report on Reddit).
- **"Automatically hide the taskbar"**: the value now hides together with the taskbar on
  every edge, and comes back when the taskbar does. With auto-hide on, GlucoBar also checks
  whether the mouse is on the taskbar or the taskbar is in use, for systems where Windows
  hides it without moving it.
- The build has a new test that moves the taskbar to every edge and turns auto-hide on, on
  Windows 10 and Windows 11.

## [0.9.3] - 2026-10-28

### Added
- **Check for updates now**: *Settings → Updates* shows the installed version, checks GitHub
  right away and, if there is a newer version, installs it with one click (on the Mac it
  opens the download page). The daily check and the automatic install are there too.

### Changed
- **Settings in tabs**, by topic: *General* (account, language, unit, how often to update,
  start with Windows), *Values and alerts* (thresholds, alerts, delta), *Appearance* (theme
  and every colour), *Elements* (what to show, size and chart on hover for the taskbar value,
  period, always on top and lock for the desktop panel) and *Updates*.
- The right-click menu is shorter: refresh, *Show*, *Sensor*, *Settings…* and quit, plus the
  few items that belong to each element (move and size for the taskbar value; chart period,
  lock and always on top for the desktop panel).

## [0.9.2] - 2026-10-28

### Added
- **Desktop panel always on top**: right-click the panel → *Always on top* keeps it over
  the other windows (for example over the browser) instead of behind them. It hides by itself
  while an app is full screen on the same monitor (a video, a presentation, a game) and comes
  back afterwards (thanks for the suggestion on Reddit). Off by default (`desktop_on_top`).
  The build checks it on Windows: above an app opened after it, hidden when that app goes
  full screen, visible again when it closes.

## [0.9.1] - 2026-10-28

### Added
- **Chart on hover**: keep the mouse on the value on the taskbar for a second and the full
  chart opens just above it, with the same content as the desktop panel (value, average,
  time in range, last hours). It fades and slides in, and fades out when the mouse leaves.
  It can be turned off from the right-click menu (`hover_chart`). The build checks it on
  Windows with the mouse: not there after 0.4 s, drawn above the value after 1.8 s, gone
  when the mouse moves away.

## [0.9.0] - 2026-10-28

### Added
- **Sensor replacement** (*Sensor* in the menu). With LibreLinkUp GlucoBar shows the day of
  use and the serial number (click to copy it), reminds you 24 hours and 2 hours before the
  sensor ends, and shows a message when the sensor seems to have stopped early (no data for an
  hour while the connection works) or was replaced more than a day early. *Request a sensor
  replacement…* opens the manufacturer's page for your country (Abbott or Dexcom) and copies
  the serial number, ready to paste into the form. Dexcom Share and Nightscout do not report
  the sensor, so for them there is only the menu item.
- **Settings window** (*Settings…* in the right-click menu): theme (light, dark or automatic,
  following Windows or macOS also when it changes), every colour, and thresholds in your
  unit. Colours are picked with the system colour picker:
  - the value: in range, high, very high, low and old value (standard, colour-blind friendly
    or your own);
  - the small window and the desktop panel, separately for the light and the dark theme:
    backgrounds, text, secondary text, chart line, grid, target range band, errors;
  - the value on the taskbar: transparent or solid background, its colour, and the minutes
    under the value.

  Every change shows right away on the taskbar, the icon, the small window and the desktop
  panel. The colours of the value can also be set with `glucobar set color_low=#0000ff`
  and so on.
- **Alerts**, off by default: low glucose, very high glucose, no new data. One message per
  episode. They do not replace your sensor's alarms, and GlucoBar says so the first time.
- **Person**: if your LibreLinkUp account follows more than one person, choose who to show.
- **Updates from GlucoBar**: once a day GlucoBar asks GitHub for the latest version. On
  Windows, *Install now* downloads the installer, checks its SHA-256 fingerprint against the
  one GitHub publishes, and installs it in silence: GlucoBar closes and reopens with the same
  settings. *Install new versions automatically* in the menu does it without asking
  (`auto_update`, off by default). Only full releases are offered, not pre-releases. On the
  Mac the notice opens the download page. The check can be turned off (`update_check`).
- After an update, GlucoBar says so once, with a link to what is new.
- **Delta**: *Show the change (delta)* in the right-click menu of the value on the taskbar
  and of the small window adds the change since the previous reading, per 5 minutes as in
  Nightscout, e.g. "3 min +5" (thanks for the suggestion on Reddit). Off by default
  (`show_delta`).
- *Start with Windows* in the menu.
- The build installs the previous release, opens it and installs the new version over it in
  silence, checking that settings, password and choices stay. It also checks the update from
  inside GlucoBar against a fake GitHub: download, fingerprint, install, reopen. New workflows: a daily check of
  the real LibreLinkUp, Dexcom Share and Nightscout services, and a weekly soak test that
  keeps GlucoBar open with a reading every 10 seconds and checks that memory and graphics
  objects do not grow.

### Fixed
- Right-clicking the value on the taskbar often opened the taskbar's own menu: with the
  transparent background, Windows passed every click that did not land exactly on a digit
  to the taskbar. Now the whole value area opens GlucoBar's menu (thanks for the report on
  Reddit).
- Choosing an item in a submenu, for example *Update every → 10 s*, could do nothing.
  Menus are now built completely before they open. Both fixes are checked in the build by
  clicking with the mouse on Windows, and the same test fails on 0.8.4.
- A silent install without `/ELEMENTS` (for example an update with winget) stayed stuck
  forever on an invisible "choose at least one element" message, with GlucoBar still open.
  Now a silent update keeps the current choices, and the guided installer starts with them
  ticked. The build now tests exactly this, both from the installer and from GlucoBar.
- Started with Windows, GlucoBar could ask for the password again: if Windows Credential
  Manager does not answer yet right after login, GlucoBar now waits up to 30 seconds before
  asking, and writes the reason in the log. `glucobar report` also lists what starts at login
  and looks like GlucoBar (for example the first script version).
- A silent update (for example with winget) reset what to show to "taskbar and icon" and the
  language to the installer's one. Now it keeps your choices, unless you pass `/ELEMENTS`,
  `/LANG` or `/SENSOR`.

### Changed
- The right-click menu is now the same everywhere (value on the taskbar, icon, small window,
  desktop panel and Mac menu bar), plus the few items that belong to each element.

## [0.8.4] - 2026-10-28

### Added
- **Update every**: a new entry in the right-click menu of every element, the icon next to
  the clock and the Mac menu bar, to choose how often GlucoBar fetches the value: 10 s,
  30 s, 1 min (default), 2 min or 5 min (thanks for the suggestion on Reddit). Any value
  from 10 to 3600 seconds works with `glucobar set refresh_seconds=...`. After an error
  (wrong password, no connection) GlucoBar still waits at least a minute before trying
  again, so the sensor service does not lock the account.

## [0.8.3] - 2026-10-28

### Fixed
- **GlucoBar closed itself when you opened an app or a folder** with the value on the
  taskbar shown (a regression in 0.8.2): the Windows notification about the foreground
  window was handled inside Tkinter's event loop.
- **No more flicker of the value on the taskbar** when you click the taskbar or close a
  window: GlucoBar now listens in its own thread to Windows' notifications about the window
  in front and the order of windows, and gets back on top only when the taskbar has gone over
  it.

### Added
- The build runs GlucoBar with the value on the taskbar, opens and closes apps and folders,
  clicks the taskbar and photographs the value every few milliseconds: the release is
  blocked if GlucoBar closes or the value disappears.

## [0.8.2] - 2026-10-27

### Fixed
- The value on the taskbar no longer flickers when you click an empty part of the taskbar or
  close a window: GlucoBar now gets back on top as soon as Windows changes the window in
  front, instead of at the next check half a second later (thanks for the report on Reddit).

## [0.8.1] - 2026-10-27

### Added
- The small window can be resized by dragging its bottom-right corner: the value, the arrow
  and the chart grow together (`window_scale`).
- The value on the taskbar has a *Size* menu (small, normal, large, extra large) in its
  right-click menu (`taskbar_scale`).

## [0.8.0] - 2026-10-27

### Added
- **Mac version (beta)**, for Macs with Apple silicon and macOS 11 or later, as
  `GlucoBar-mac.dmg`:
  - the value and trend arrow in the **menu bar**, next to the clock, with the GlucoBar menu;
  - the small window and the desktop panel, as on Windows;
  - passwords in the macOS Keychain, settings in `~/Library/Application Support/GlucoBar`;
  - *Open at login* from the menu (or `glucobar set autostart=true`);
  - the `glucobar` command inside the app.

  Built and tested by GitHub Actions on a real Mac, including a live run with the value in
  the menu bar. The app is not notarized by Apple yet: the first time, allow it in
  System Settings → Privacy & Security → Open Anyway.

## [0.7.2] - 2026-10-27

### Changed
- Uninstalling or updating GlucoBar while it is running no longer asks you to close it:
  the installer closes it by itself (the icon disappears from the clock right away), and a
  silent update (e.g. winget) opens it again afterwards.

### Added
- `glucobar stop` closes GlucoBar from a terminal.

## [0.7.1] - 2026-10-27

### Changed
- The number in the icon next to the clock now fills the whole height of the icon, with
  taller, narrower digits: much easier to read at taskbar size (thanks for the feedback on
  Reddit).
- If Microsoft Defender flags a new installer on VirusTotal (a false positive that has to be
  reported to Microsoft), the release is published as a pre-release, so the main download
  link keeps giving the previous version until it is cleared.

## [0.7.0] - 2026-10-27

### Added
- **Nightscout (beta)**: readings from your own Nightscout site, so any sensor that uploads
  to Nightscout works (Medtronic, Eversense, xDrip+, Juggluco, AndroidAPS, Loop…). Public
  sites need only the address; private ones a read-only token (or the API secret). The
  installer, the first start and `glucobar setup` offer it as a third sensor
  (`/SENSOR=nightscout`, `glucobar set source=nightscout`).
- The same option works with **Nocturne**, the successor of Nightscout from the Nightscout
  organisation: it serves the same API and accepts its `noc_…` API tokens.
- Each release also includes `GlucoBar-Setup.exe`, the same installer under a fixed name, so
  https://github.com/jackfaz/glucobar/releases/latest/download/GlucoBar-Setup.exe always
  downloads the latest version.

## [0.6.0] - 2026-10-27

### Added
- **Dexcom (beta)**: G6, G7 and ONE+ readings through Dexcom Share, with your own Dexcom
  account (email, phone number or user name) and the region where it was created. Tested
  against a simulated Dexcom Share server; feedback from Dexcom users is welcome.
- The installer asks which sensor you use and shows the setup steps for it (LibreLinkUp or
  Dexcom Share), with a link to the illustrated guide. The choice is preselected on first
  start. Silent install: `/SENSOR=libre` or `/SENSOR=dexcom`.
- On first start and with *Change account…*, GlucoBar asks which sensor you use.
  `glucobar setup` and `glucobar login` ask too, and `glucobar set source=dexcom
  dexcom_region=us` works from scripts.

### Changed
- Windows 11: the icon next to the clock is now shown on the taskbar right away, instead of
  under the ^ arrow (once: if you move it back under the arrow, it stays there).
- LibreLinkUp: the README has a step-by-step guide, and the installer and the app now say
  that the LibreLinkUp account can be the same as your LibreLink account (sharing with
  yourself), which is the simplest setup.
- Each sensor service has its own entry in Windows Credential Manager
  (`GlucoBar:LibreLinkUp`, `GlucoBar:Dexcom`); deleting everything removes both.
- `glucobar report` shows the real display scaling, and the log records where the value on
  the taskbar really is and why it is hidden, to track down cases where it does not appear.
- The PyInstaller bootloader is built from source in CI, and test builds can be scanned on
  VirusTotal (*Run workflow* → *scan*), with the results shown in the build summary.

## [0.5.2] - 2026-10-27

### Added
- Each release lists the installer's SHA-256 and a link to its VirusTotal scan.
- Code signing policy in the README (roles and privacy), ready for a SignPath Foundation
  application.

### Changed
- `GlucoBar.exe` and `glucobar-cli.exe` now carry name, description and version in their file
  properties.

## [0.5.1] - 2026-10-27

### Added
- `glucobar report`: a diagnostic summary for bug reports (versions, screens, settings, last
  log lines), copied to the clipboard. Email, user name and glucose values are hidden.
- Bug report form on GitHub, with the commands to collect that summary; questions and ideas
  go to Discussions.

## [0.5.0] - 2026-10-27

### Added
- **`glucobar` command** in any terminal (the installer adds it to your PATH):
  - `glucobar setup`: interactive setup with arrow keys and checkboxes: language, what to
    show, unit, target range, monitor, LibreLinkUp account with a live connection test,
    start with Windows. Nothing is saved until the end; Esc cancels.
  - `glucobar status`: the current reading in the terminal.
  - `glucobar set key=value …` / `glucobar get`: change or show settings, for scripts too.
  - `glucobar login`, `glucobar start`, `glucobar forget`.
- A running GlucoBar picks up settings changed from the terminal within two seconds, without
  restarting.
- Silent install with choices, e.g. `/VERYSILENT /ELEMENTS=desktop,tray /LANG=it`.
- winget manifest generated for each release.
- Releases can be published from the Actions page (*Run workflow* → *release*).

### Changed
- Installer: nothing is ticked at first, and the preview shows exactly the ticked elements
  together (base desktop plus one layer per element), in the installer's language.
- README: plainer wording, and a list of supported and planned sensors (Dexcom in progress).
- "Start with Windows" now uses the registry `Run` entry instead of a Startup-folder
  shortcut, so it can also be switched with `glucobar set autostart=true|false`.
- The build now also tests the `glucobar` command, PATH and autostart after a silent install,
  and checks that uninstalling removes them.

## [0.4.0] - 2026-10-27

### Added
- The installer always asks for the language first; the chosen language becomes GlucoBar's
  language too.
- `GlucoBar.exe --forget` deletes the saved password, settings, log and the first-version
  settings file. The uninstaller uses it when you choose to delete everything.
- Changelog (this file), used as the text of each GitHub release.

### Fixed
- **Privacy:** after uninstalling with "delete settings and password", GlucoBar was still
  signed in after reinstalling. The password was imported again from the plain-text
  `.glicemia_widget.json` of the first (script) version. Now the password is removed from that
  file right after importing it, the file is never imported twice, and existing installs clean
  it up on first start.
- The uninstaller now asks *before* removing files, so GlucoBar itself can delete the password
  from Windows Credential Manager.

### Changed
- The build now also installs GlucoBar silently, checks that `--forget` really removes the
  password from Windows Credential Manager, and uninstalls it again.

## [0.3.0] - 2026-10-27

### Added
- Combine what to show: value on the taskbar, icon next to the clock, small window and desktop
  panel can be shown in any combination (at least one). The icon is optional.
- *Show* menu with checkboxes, both on the icon and when right-clicking any element.
- Installer: checkboxes instead of a single mode, with preview and description of the last
  clicked item.
- More realistic previews of the Windows 11 taskbar.

### Changed
- Settings from 0.2.0 (`mode`) are converted automatically to the new `elements` list.

### Fixed
- Installer error "Could not call proc" on start: default checkboxes were ticked before the
  preview was created. The build now runs the installer to catch this kind of error.

## [0.2.0] - 2026-10-27

### Added
- **Desktop panel**: a resizable panel behind your windows with a large chart (3, 6 or 12
  hours), average, min, max, time in range, 15-minute change and sensor day.
- A single GlucoBar icon next to the clock showing the value and a menu to switch mode, unit,
  language and account, or quit.
- Six languages: English, Italian, Spanish, French, German, Portuguese.
- Installer page to choose the mode, with a preview in the installer's language.
- First-start notification explaining where the icon is (Windows 11 hides new icons under ^).

### Changed
- One GlucoBar process at a time; modes switch without restarting.

### Fixed
- The process now always exits on *Quit*, so GlucoBar can be started again.

## [0.1.0] - 2026-10-27

### Added
- First release as an installable Windows app (previously a set of Python scripts).
- Three modes: value on the taskbar (also on a second monitor, hidden during full-screen
  apps), small always-on-top window with chart, number icon in the notification area.
- LibreLinkUp client with automatic region redirect and minimum app version.
- Password stored in Windows Credential Manager; automatic import of the first version's
  settings.
- Italian and English interface.
- Inno Setup installer and GitHub Actions build.

[0.11.2]: https://github.com/jackfaz/glucobar/releases/tag/v0.11.2
[0.11.1]: https://github.com/jackfaz/glucobar/releases/tag/v0.11.1
[0.11.0]: https://github.com/jackfaz/glucobar/releases/tag/v0.11.0
[0.10.1]: https://github.com/jackfaz/glucobar/releases/tag/v0.10.1
[0.10.0]: https://github.com/jackfaz/glucobar/releases/tag/v0.10.0
[0.9.8]: https://github.com/jackfaz/glucobar/releases/tag/v0.9.8
[0.9.7]: https://github.com/jackfaz/glucobar/releases/tag/v0.9.7
[0.9.6]: https://github.com/jackfaz/glucobar/releases/tag/v0.9.6
[0.9.5]: https://github.com/jackfaz/glucobar/releases/tag/v0.9.5
[0.9.4]: https://github.com/jackfaz/glucobar/releases/tag/v0.9.4
[0.9.3]: https://github.com/jackfaz/glucobar/releases/tag/v0.9.3
[0.9.2]: https://github.com/jackfaz/glucobar/releases/tag/v0.9.2
[0.9.1]: https://github.com/jackfaz/glucobar/releases/tag/v0.9.1
[0.9.0]: https://github.com/jackfaz/glucobar/releases/tag/v0.9.0
[0.8.4]: https://github.com/jackfaz/glucobar/releases/tag/v0.8.4
[0.8.3]: https://github.com/jackfaz/glucobar/releases/tag/v0.8.3
[0.8.2]: https://github.com/jackfaz/glucobar/releases/tag/v0.8.2
[0.8.1]: https://github.com/jackfaz/glucobar/releases/tag/v0.8.1
[0.8.0]: https://github.com/jackfaz/glucobar/releases/tag/v0.8.0
[0.7.2]: https://github.com/jackfaz/glucobar/releases/tag/v0.7.2
[0.7.1]: https://github.com/jackfaz/glucobar/releases/tag/v0.7.1
[0.7.0]: https://github.com/jackfaz/glucobar/releases/tag/v0.7.0
[0.6.0]: https://github.com/jackfaz/glucobar/releases/tag/v0.6.0
[0.5.2]: https://github.com/jackfaz/glucobar/releases/tag/v0.5.2
[0.5.1]: https://github.com/jackfaz/glucobar/releases/tag/v0.5.1

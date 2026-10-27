# Changelog

All notable changes to GlucoBar are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
uses [Semantic Versioning](https://semver.org/).

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

[0.8.1]: https://github.com/jackfaz/glucobar/releases/tag/v0.8.1
[0.8.0]: https://github.com/jackfaz/glucobar/releases/tag/v0.8.0
[0.7.2]: https://github.com/jackfaz/glucobar/releases/tag/v0.7.2
[0.7.1]: https://github.com/jackfaz/glucobar/releases/tag/v0.7.1
[0.7.0]: https://github.com/jackfaz/glucobar/releases/tag/v0.7.0
[0.6.0]: https://github.com/jackfaz/glucobar/releases/tag/v0.6.0
[0.5.2]: https://github.com/jackfaz/glucobar/releases/tag/v0.5.2
[0.5.1]: https://github.com/jackfaz/glucobar/releases/tag/v0.5.1

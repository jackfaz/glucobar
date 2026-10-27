# Changelog

All notable changes to GlucoBar are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
uses [Semantic Versioning](https://semver.org/).

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

[0.5.1]: https://github.com/jackfaz/glucobar/releases/tag/v0.5.1

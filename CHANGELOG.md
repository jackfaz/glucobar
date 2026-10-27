# Changelog

All notable changes to GlucoBar are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
uses [Semantic Versioning](https://semver.org/).

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

[0.4.0]: https://github.com/jackfaz/glucobar/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/jackfaz/glucobar/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jackfaz/glucobar/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jackfaz/glucobar/releases/tag/v0.1.0

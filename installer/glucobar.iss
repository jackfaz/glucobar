; Installer di GlucoBar (Inno Setup 6)
; Compilazione: iscc /DAppVersion=0.1.0 installer\glucobar.iss
; Prima serve l'exe: pyinstaller --noconfirm --clean glucobar.spec

#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
#ifndef RepoUrl
  #define RepoUrl "https://github.com/"
#endif

[Setup]
AppId={{08BF5F70-5160-4B58-BCA3-99FF0D35CACC}
AppName=GlucoBar
AppVersion={#AppVersion}
AppVerName=GlucoBar {#AppVersion}
AppPublisher=GlucoBar contributors
AppPublisherURL={#RepoUrl}
AppSupportURL={#RepoUrl}/issues
AppUpdatesURL={#RepoUrl}/releases
; Installazione per l'utente corrente: niente richiesta di amministratore
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\GlucoBar
DefaultGroupName=GlucoBar
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist-installer
OutputBaseFilename=GlucoBar-Setup-{#AppVersion}
SetupIconFile=..\assets\glucobar.ico
UninstallDisplayIcon={app}\GlucoBar.exe
UninstallDisplayName=GlucoBar
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Stessi nomi dei mutex creati da glucobar/app.py
AppMutex=GlucoBar-taskbar,GlucoBar-window,GlucoBar-tray
CloseApplications=yes

[Languages]
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"; InfoBeforeFile: "disclaimer-it.txt"
Name: "en"; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: "disclaimer-en.txt"

[CustomMessages]
it.TypeRecommended=Consigliata (glicemia sulla barra delle applicazioni)
it.TypeFull=Completa (tutte le modalità)
it.TypeCustom=Personalizzata
it.CompTaskbar=Sulla barra delle applicazioni, accanto all'orologio
it.CompWindow=Finestrella con grafico, sempre in primo piano
it.CompTray=Icona col numero nell'area di notifica
it.NameTaskbar=Barra
it.NameWindow=Finestra
it.NameTray=Icona
it.TaskAutostart=Avvia GlucoBar all'accensione del PC
it.GroupStartup=Avvio:
it.LaunchTaskbar=Avvia GlucoBar sulla barra adesso
it.LaunchWindow=Avvia la finestrella adesso
it.LaunchTray=Avvia l'icona adesso
it.NeedOneComponent=Scegli almeno una modalità di GlucoBar.
it.RemoveSettings=Vuoi eliminare anche le impostazioni e la password LibreLinkUp salvata su questo PC?
en.TypeRecommended=Recommended (glucose on the taskbar)
en.TypeFull=Full (all modes)
en.TypeCustom=Custom
en.CompTaskbar=On the taskbar, next to the clock
en.CompWindow=Small always-on-top window with chart
en.CompTray=Number icon in the notification area
en.NameTaskbar=Taskbar
en.NameWindow=Window
en.NameTray=Icon
en.TaskAutostart=Start GlucoBar when Windows starts
en.GroupStartup=Startup:
en.LaunchTaskbar=Start GlucoBar on the taskbar now
en.LaunchWindow=Start the small window now
en.LaunchTray=Start the icon now
en.NeedOneComponent=Please choose at least one GlucoBar mode.
en.RemoveSettings=Do you also want to delete the settings and the LibreLinkUp password saved on this PC?

[Types]
Name: "recommended"; Description: "{cm:TypeRecommended}"
Name: "full"; Description: "{cm:TypeFull}"
Name: "custom"; Description: "{cm:TypeCustom}"; Flags: iscustom

[Components]
Name: "taskbar"; Description: "{cm:CompTaskbar}"; Types: recommended full
Name: "window"; Description: "{cm:CompWindow}"; Types: full
Name: "tray"; Description: "{cm:CompTray}"; Types: full

[Tasks]
Name: "autostart"; Description: "{cm:TaskAutostart}"; GroupDescription: "{cm:GroupStartup}"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\GlucoBar\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\GlucoBar - {cm:NameTaskbar}"; Filename: "{app}\GlucoBar.exe"; Parameters: "--mode taskbar"; Components: taskbar
Name: "{group}\GlucoBar - {cm:NameWindow}"; Filename: "{app}\GlucoBar.exe"; Parameters: "--mode window"; Components: window
Name: "{group}\GlucoBar - {cm:NameTray}"; Filename: "{app}\GlucoBar.exe"; Parameters: "--mode tray"; Components: tray
Name: "{group}\{cm:UninstallProgram,GlucoBar}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\GlucoBar - {cm:NameTaskbar}"; Filename: "{app}\GlucoBar.exe"; Parameters: "--mode taskbar"; Components: taskbar; Tasks: desktopicon
Name: "{autodesktop}\GlucoBar - {cm:NameWindow}"; Filename: "{app}\GlucoBar.exe"; Parameters: "--mode window"; Components: window; Tasks: desktopicon
Name: "{autodesktop}\GlucoBar - {cm:NameTray}"; Filename: "{app}\GlucoBar.exe"; Parameters: "--mode tray"; Components: tray; Tasks: desktopicon
Name: "{userstartup}\GlucoBar - {cm:NameTaskbar}"; Filename: "{app}\GlucoBar.exe"; Parameters: "--mode taskbar"; Components: taskbar; Tasks: autostart
Name: "{userstartup}\GlucoBar - {cm:NameWindow}"; Filename: "{app}\GlucoBar.exe"; Parameters: "--mode window"; Components: window; Tasks: autostart
Name: "{userstartup}\GlucoBar - {cm:NameTray}"; Filename: "{app}\GlucoBar.exe"; Parameters: "--mode tray"; Components: tray; Tasks: autostart

[Run]
Filename: "{app}\GlucoBar.exe"; Parameters: "--mode taskbar"; Description: "{cm:LaunchTaskbar}"; Flags: nowait postinstall skipifsilent; Components: taskbar
Filename: "{app}\GlucoBar.exe"; Parameters: "--mode window"; Description: "{cm:LaunchWindow}"; Flags: nowait postinstall skipifsilent unchecked; Components: window
Filename: "{app}\GlucoBar.exe"; Parameters: "--mode tray"; Description: "{cm:LaunchTray}"; Flags: nowait postinstall skipifsilent unchecked; Components: tray

[Code]
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = wpSelectComponents) and
     not WizardIsComponentSelected('taskbar') and
     not WizardIsComponentSelected('window') and
     not WizardIsComponentSelected('tray') then
  begin
    MsgBox(CustomMessage('NeedOneComponent'), mbError, MB_OK);
    Result := False;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if (CurUninstallStep = usPostUninstall) and not UninstallSilent then
    if MsgBox(CustomMessage('RemoveSettings'), mbConfirmation,
              MB_YESNO or MB_DEFBUTTON2) = IDYES then
    begin
      DelTree(ExpandConstant('{userappdata}\GlucoBar'), True, True, True);
      // Password nel Gestione credenziali (vedi glucobar/credentials.py)
      Exec(ExpandConstant('{sys}\cmdkey.exe'), '/delete:GlucoBar:LibreLinkUp', '',
           SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
end;

; Installer di GlucoBar (Inno Setup 6)
; Prima servono l'exe e le anteprime:
;   pyinstaller --noconfirm --clean glucobar.spec
;   python tools\previews_to_bmp.py
; Poi: iscc /DAppVersion=0.5.2 installer\glucobar.iss
; Installazione silenziosa con scelte: /VERYSILENT /ELEMENTS=desktop,tray /LANG=it

#ifndef AppVersion
  #define AppVersion "0.5.2"
#endif
#ifndef RepoUrl
  #define RepoUrl "https://github.com/"
#endif
; posizioni dei ritagli dell'anteprima (generato da tools\previews_to_bmp.py)
#include "build\preview_layout.iss"

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
; Stesso nome del mutex creato da glucobar/app.py
AppMutex=GlucoBar
CloseApplications=yes
; chiede sempre la lingua all'avvio: diventa anche la lingua di GlucoBar
ShowLanguageDialog=yes
; il comando "glucobar" va nel PATH dell'utente: avvisa i terminali nuovi
ChangesEnvironment=yes

[Languages]
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"; InfoBeforeFile: "disclaimer-it.txt"
Name: "en"; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: "disclaimer-en.txt"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"; InfoBeforeFile: "disclaimer-es.txt"
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"; InfoBeforeFile: "disclaimer-fr.txt"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"; InfoBeforeFile: "disclaimer-de.txt"
Name: "pt"; MessagesFile: "compiler:Languages\Portuguese.isl"; InfoBeforeFile: "disclaimer-pt.txt"

[CustomMessages]
it.ModeTitle=Scegli cosa mostrare
it.ModeSubtitle=Puoi sceglierne più di uno e cambiarli quando vuoi col clic destro su GlucoBar.
it.Name_taskbar=Sulla barra delle applicazioni
it.Name_window=Finestrella
it.Name_desktop=Pannello sullo sfondo
it.Name_tray=Icona vicino all'orologio
it.Desc_taskbar=Valore, freccia e minuti sulla barra, accanto all'orologio. Funziona anche sul secondo monitor e si nasconde con i video a schermo intero.
it.Desc_window=Piccola finestra sempre in primo piano con valore e grafico delle ultime 3 ore. La trascini dove vuoi.
it.Desc_desktop=Pannello sul desktop, dietro le finestre: grafico grande fino a 12 ore, media, minimo, massimo e tempo nel range. Ridimensionabile.
it.Desc_tray=Il numero colorato nell'icona vicino all'orologio; passandoci sopra vedi freccia e minuti. Col clic destro apri il menu.
it.TaskAutostart=Avvia GlucoBar all'accensione del PC
it.GroupStartup=Avvio:
it.LaunchNow=Avvia GlucoBar adesso
it.RemoveSettings=Vuoi eliminare anche le impostazioni e le password (LibreLinkUp, Dexcom) salvate su questo PC?
it.NeedOne=Scegli almeno un elemento da mostrare.
it.PreviewHint=Spunta cosa vuoi vedere: l'anteprima mostra la tua combinazione.
en.ModeTitle=Choose what to show
en.ModeSubtitle=You can pick more than one and change them any time by right-clicking GlucoBar.
en.Name_taskbar=On the taskbar
en.Name_window=Small window
en.Name_desktop=Desktop panel
en.Name_tray=Icon next to the clock
en.Desc_taskbar=Value, arrow and minutes on the taskbar, next to the clock. Works on a second monitor too and hides during full-screen videos.
en.Desc_window=Small always-on-top window with the value and a 3-hour chart. Drag it anywhere.
en.Desc_desktop=Panel on the desktop, behind your windows: large chart up to 12 hours, average, min, max and time in range. Resizable.
en.Desc_tray=The colored number in the icon next to the clock; hover it for arrow and minutes. Right-click it for the menu.
en.TaskAutostart=Start GlucoBar when Windows starts
en.GroupStartup=Startup:
en.LaunchNow=Start GlucoBar now
en.RemoveSettings=Do you also want to delete the settings and the passwords (LibreLinkUp, Dexcom) saved on this PC?
en.NeedOne=Please choose at least one thing to show.
en.PreviewHint=Tick what you want to see: the preview shows your combination.
es.ModeTitle=Elige qué mostrar
es.ModeSubtitle=Puedes elegir más de uno y cambiarlos cuando quieras con clic derecho en GlucoBar.
es.Name_taskbar=En la barra de tareas
es.Name_window=Ventana pequeña
es.Name_desktop=Panel en el escritorio
es.Name_tray=Icono junto al reloj
es.Desc_taskbar=Valor, flecha y minutos en la barra, junto al reloj. Funciona también en un segundo monitor y se oculta con vídeos a pantalla completa.
es.Desc_window=Ventana pequeña siempre visible con el valor y un gráfico de 3 horas. Arrástrala donde quieras.
es.Desc_desktop=Panel en el escritorio, detrás de las ventanas: gráfico grande de hasta 12 horas, media, mínimo, máximo y tiempo en rango. Redimensionable.
es.Desc_tray=El número en color en el icono junto al reloj; pasa el ratón para ver flecha y minutos. Clic derecho para el menú.
es.TaskAutostart=Iniciar GlucoBar al encender el PC
es.GroupStartup=Inicio:
es.LaunchNow=Iniciar GlucoBar ahora
es.RemoveSettings=¿Quieres borrar también los ajustes y las contraseñas (LibreLinkUp, Dexcom) guardadas en este PC?
es.NeedOne=Elige al menos un elemento para mostrar.
es.PreviewHint=Marca lo que quieres ver: la vista previa muestra tu combinación.
fr.ModeTitle=Choisissez quoi afficher
fr.ModeSubtitle=Vous pouvez en choisir plusieurs et les changer à tout moment par clic droit sur GlucoBar.
fr.Name_taskbar=Sur la barre des tâches
fr.Name_window=Petite fenêtre
fr.Name_desktop=Panneau sur le bureau
fr.Name_tray=Icône près de l'horloge
fr.Desc_taskbar=Valeur, flèche et minutes sur la barre, près de l'horloge. Fonctionne aussi sur un second écran et se masque pendant les vidéos plein écran.
fr.Desc_window=Petite fenêtre toujours au premier plan avec la valeur et un graphique de 3 heures. Déplacez-la où vous voulez.
fr.Desc_desktop=Panneau sur le bureau, derrière les fenêtres : grand graphique jusqu'à 12 heures, moyenne, min, max et temps dans la cible. Redimensionnable.
fr.Desc_tray=Le chiffre en couleur dans l'icône près de l'horloge ; survolez-la pour la flèche et les minutes. Clic droit pour le menu.
fr.TaskAutostart=Lancer GlucoBar au démarrage de Windows
fr.GroupStartup=Démarrage :
fr.LaunchNow=Lancer GlucoBar maintenant
fr.RemoveSettings=Voulez-vous aussi supprimer les réglages et les mots de passe (LibreLinkUp, Dexcom) enregistrés sur ce PC ?
fr.NeedOne=Choisissez au moins un élément à afficher.
fr.PreviewHint=Cochez ce que vous voulez voir : l'aperçu montre votre combinaison.
de.ModeTitle=Wähle, was angezeigt wird
de.ModeSubtitle=Du kannst mehrere wählen und sie jederzeit per Rechtsklick auf GlucoBar ändern.
de.Name_taskbar=Auf der Taskleiste
de.Name_window=Kleines Fenster
de.Name_desktop=Desktop-Panel
de.Name_tray=Symbol neben der Uhr
de.Desc_taskbar=Wert, Pfeil und Minuten auf der Taskleiste neben der Uhr. Funktioniert auch auf einem zweiten Monitor und verschwindet bei Vollbild-Videos.
de.Desc_window=Kleines Fenster immer im Vordergrund mit Wert und 3-Stunden-Grafik. Frei verschiebbar.
de.Desc_desktop=Panel auf dem Desktop hinter den Fenstern: große Grafik bis 12 Stunden, Mittelwert, Min, Max und Zeit im Zielbereich. Größe veränderbar.
de.Desc_tray=Die farbige Zahl im Symbol neben der Uhr; mit der Maus darüber siehst du Pfeil und Minuten. Rechtsklick öffnet das Menü.
de.TaskAutostart=GlucoBar beim Start von Windows öffnen
de.GroupStartup=Start:
de.LaunchNow=GlucoBar jetzt starten
de.RemoveSettings=Sollen auch die Einstellungen und die auf diesem PC gespeicherten Passwörter (LibreLinkUp, Dexcom) gelöscht werden?
de.NeedOne=Bitte wähle mindestens ein Element aus.
de.PreviewHint=Kreuze an, was du sehen möchtest: die Vorschau zeigt deine Auswahl.
pt.ModeTitle=Escolha o que mostrar
pt.ModeSubtitle=Pode escolher mais de um e mudá-los quando quiser com clique direito no GlucoBar.
pt.Name_taskbar=Na barra de tarefas
pt.Name_window=Janela pequena
pt.Name_desktop=Painel no ambiente de trabalho
pt.Name_tray=Ícone junto ao relógio
pt.Desc_taskbar=Valor, seta e minutos na barra, junto ao relógio. Funciona também num segundo monitor e esconde-se durante vídeos em ecrã inteiro.
pt.Desc_window=Janela pequena sempre visível com o valor e um gráfico de 3 horas. Arraste-a para onde quiser.
pt.Desc_desktop=Painel no ambiente de trabalho, atrás das janelas: gráfico grande até 12 horas, média, mínimo, máximo e tempo no alvo. Redimensionável.
pt.Desc_tray=O número colorido no ícone junto ao relógio; passe o rato para ver seta e minutos. Clique direito para o menu.
pt.TaskAutostart=Iniciar o GlucoBar ao ligar o PC
pt.GroupStartup=Arranque:
pt.LaunchNow=Iniciar o GlucoBar agora
pt.RemoveSettings=Quer apagar também as definições e as palavras-passe (LibreLinkUp, Dexcom) guardadas neste PC?
pt.NeedOne=Escolha pelo menos um elemento para mostrar.
pt.PreviewHint=Marque o que quer ver: a pré-visualização mostra a sua combinação.

[Tasks]
Name: "autostart"; Description: "{cm:TaskAutostart}"; GroupDescription: "{cm:GroupStartup}"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\GlucoBar\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; il comando "glucobar" da terminale (richiama glucobar-cli.exe)
Source: "glucobar.cmd"; DestDir: "{app}\bin"; Flags: ignoreversion
; anteprime della pagina "Scegli la modalità" (non vengono installate)
Source: "build\previews\*.bmp"; Flags: dontcopy

[InstallDelete]
; collegamenti della 0.1.0, che aveva un collegamento per modalità
Type: files; Name: "{group}\GlucoBar - *.lnk"
Type: files; Name: "{userstartup}\GlucoBar - *.lnk"
Type: files; Name: "{autodesktop}\GlucoBar - *.lnk"
; 0.2.0-0.4.0: avvio automatico con un collegamento (ora è nel registro, vedi [Registry])
Type: files; Name: "{userstartup}\GlucoBar.lnk"

[Registry]
; avvio con Windows: la stessa voce che gestisce "glucobar set autostart=..."
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "GlucoBar"; ValueData: """{app}\GlucoBar.exe"""; Tasks: autostart; Flags: uninsdeletevalue
; "glucobar" in ogni terminale nuovo
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\bin"; Check: NeedsAddPath(ExpandConstant('{app}\bin'))

[Icons]
Name: "{group}\GlucoBar"; Filename: "{app}\GlucoBar.exe"
Name: "{group}\{cm:UninstallProgram,GlucoBar}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\GlucoBar"; Filename: "{app}\GlucoBar.exe"; Tasks: desktopicon

[Run]
; salva elementi e lingua scelti (anche se GlucoBar non viene avviato subito)
Filename: "{app}\GlucoBar.exe"; Parameters: "--set-elements {code:SelectedElements} --set-language {language}"; Flags: runhidden waituntilterminated
Filename: "{app}\GlucoBar.exe"; Description: "{cm:LaunchNow}"; Flags: nowait postinstall skipifsilent

[Code]
var
  ModePage: TWizardPage;
  ModeBoxes: array of TNewCheckBox;
  ModePreview: TBitmapImage;          // il desktop vuoto
  ModeLayers: array of TBitmapImage;  // un ritaglio per elemento, sopra la base
  ModeDescription: TNewStaticText;
  LastClicked: Integer;

{ Stesso ordine di ELEMENTS in glucobar/config.py }
function ModeId(I: Integer): String;
begin
  case I of
    0: Result := 'taskbar';
    1: Result := 'tray';
    2: Result := 'window';
  else
    Result := 'desktop';
  end;
end;

{ Immagini nella lingua dell'installazione, es. it_base.bmp, it_taskbar.bmp }
function PreviewFile(Name: String): String;
begin
  Result := ActiveLanguage + '_' + Name + '.bmp';
end;

// Dove va il ritaglio sulla base, in pixel dell'immagine (vedi preview_layout.iss)
procedure LayerRect(I: Integer; var X, Y, W, H: Integer);
begin
  case I of
    0: begin X := {#Layer_taskbar_x}; Y := {#Layer_taskbar_y}; W := {#Layer_taskbar_w}; H := {#Layer_taskbar_h}; end;
    1: begin X := {#Layer_tray_x}; Y := {#Layer_tray_y}; W := {#Layer_tray_w}; H := {#Layer_tray_h}; end;
    2: begin X := {#Layer_window_x}; Y := {#Layer_window_y}; W := {#Layer_window_w}; H := {#Layer_window_h}; end;
  else
    begin X := {#Layer_desktop_x}; Y := {#Layer_desktop_y}; W := {#Layer_desktop_w}; H := {#Layer_desktop_h}; end;
  end;
end;

{ L'anteprima mostra insieme tutti e soli gli elementi spuntati; la descrizione
  è quella dell'ultimo spuntato, o un suggerimento se non ce n'è nessuno }
procedure UpdatePreview;
var
  I, Shown: Integer;
begin
  if (ModePreview = nil) or (ModeDescription = nil) then
    Exit;
  Shown := -1;
  for I := 0 to 3 do
  begin
    ModeLayers[I].Visible := ModeBoxes[I].Checked;
    if ModeBoxes[I].Checked and (Shown < 0) then
      Shown := I;
  end;
  if (LastClicked >= 0) and ModeBoxes[LastClicked].Checked then
    Shown := LastClicked;
  if Shown >= 0 then
    ModeDescription.Caption := CustomMessage('Desc_' + ModeId(Shown))
  else
    ModeDescription.Caption := CustomMessage('PreviewHint');
end;

procedure ModeClick(Sender: TObject);
var
  I: Integer;
begin
  for I := 0 to 3 do
    if Sender = ModeBoxes[I] then
      LastClicked := I;
  UpdatePreview;
end;

{ Coordinata dell'immagine (0..Size) -> pixel sullo schermo (0..Shown) }
function ScaleTo(Value, Size, Shown: Integer): Integer;
begin
  Result := Value * Shown div Size;
end;

procedure InitializeWizard;
var
  I, ListWidth, Gap, X, Y, W, H: Integer;
  Elements: String;
begin
  LastClicked := -1;
  ModePage := CreateCustomPage(wpInfoBefore, CustomMessage('ModeTitle'),
                               CustomMessage('ModeSubtitle'));
  ListWidth := ScaleX(170);
  Gap := ScaleX(12);

  SetArrayLength(ModeBoxes, 4);
  for I := 0 to 3 do
  begin
    ModeBoxes[I] := TNewCheckBox.Create(ModePage);
    ModeBoxes[I].Parent := ModePage.Surface;
    ModeBoxes[I].Caption := CustomMessage('Name_' + ModeId(I));
    ModeBoxes[I].Left := 0;
    ModeBoxes[I].Top := ScaleY(4) + I * ScaleY(26);
    ModeBoxes[I].Width := ListWidth;
    ModeBoxes[I].OnClick := @ModeClick;
  end;

  ExtractTemporaryFile(PreviewFile('base'));
  ModePreview := TBitmapImage.Create(ModePage);
  ModePreview.Parent := ModePage.Surface;
  ModePreview.Left := ListWidth + Gap;
  ModePreview.Top := 0;
  ModePreview.Width := ModePage.SurfaceWidth - ListWidth - Gap;
  ModePreview.Height := ModePreview.Width * {#PreviewH} div {#PreviewW};
  if ModePreview.Height > ModePage.SurfaceHeight then
  begin
    ModePreview.Height := ModePage.SurfaceHeight;
    ModePreview.Width := ModePreview.Height * {#PreviewW} div {#PreviewH};
  end;
  ModePreview.Stretch := True;
  ModePreview.Bitmap.LoadFromFile(ExpandConstant('{tmp}\') + PreviewFile('base'));

  { i ritagli, creati dopo la base così le stanno sopra; nascosti finché non si spunta }
  SetArrayLength(ModeLayers, 4);
  for I := 0 to 3 do
  begin
    ExtractTemporaryFile(PreviewFile(ModeId(I)));
    LayerRect(I, X, Y, W, H);
    ModeLayers[I] := TBitmapImage.Create(ModePage);
    ModeLayers[I].Parent := ModePage.Surface;
    ModeLayers[I].Left := ModePreview.Left + ScaleTo(X, {#PreviewW}, ModePreview.Width);
    ModeLayers[I].Top := ModePreview.Top + ScaleTo(Y, {#PreviewH}, ModePreview.Height);
    { bordo destro/basso calcolati a parte: niente fessure di un pixel }
    ModeLayers[I].Width := ScaleTo(X + W, {#PreviewW}, ModePreview.Width)
                           - ScaleTo(X, {#PreviewW}, ModePreview.Width);
    ModeLayers[I].Height := ScaleTo(Y + H, {#PreviewH}, ModePreview.Height)
                            - ScaleTo(Y, {#PreviewH}, ModePreview.Height);
    ModeLayers[I].Stretch := True;
    ModeLayers[I].Bitmap.LoadFromFile(ExpandConstant('{tmp}\') + PreviewFile(ModeId(I)));
    ModeLayers[I].Visible := False;
  end;

  ModeDescription := TNewStaticText.Create(ModePage);
  ModeDescription.Parent := ModePage.Surface;
  ModeDescription.Left := 0;
  ModeDescription.Top := ScaleY(4) + 4 * ScaleY(26) + ScaleY(8);
  ModeDescription.AutoSize := False;
  ModeDescription.WordWrap := True;
  ModeDescription.Width := ListWidth;
  ModeDescription.Height := ModePage.SurfaceHeight - ModeDescription.Top;

  { Nessuna casella spuntata all'inizio: si sceglie guardando l'anteprima.
    Da riga di comando (anche winget): /ELEMENTS=desktop,tray }
  Elements := Lowercase(ExpandConstant('{param:ELEMENTS|}'));
  if Elements <> '' then
    for I := 0 to 3 do
      ModeBoxes[I].Checked := Pos(',' + ModeId(I) + ',', ',' + Elements + ',') > 0;
  UpdatePreview;
end;

{ Almeno un elemento da mostrare }
function NextButtonClick(CurPageID: Integer): Boolean;
var
  I: Integer;
begin
  Result := True;
  if CurPageID = ModePage.ID then
  begin
    Result := False;
    for I := 0 to 3 do
      if ModeBoxes[I].Checked then
        Result := True;
    if not Result then
      MsgBox(CustomMessage('NeedOne'), mbError, MB_OK);
  end;
end;

{ Usata da [Run]: gli elementi spuntati, es. "taskbar,tray" }
function SelectedElements(Param: String): String;
var
  I: Integer;
begin
  Result := '';
  for I := 0 to 3 do
    if ModeBoxes[I].Checked then
    begin
      if Result <> '' then
        Result := Result + ',';
      Result := Result + ModeId(I);
    end;
  if Result = '' then
    Result := 'taskbar,tray';   { /ELEMENTS sbagliato: i predefiniti }
end;

// [Registry]: aggiunge {app}\bin al PATH solo se non c'è già
function NeedsAddPath(Dir: String): Boolean;
var
  Path: String;
begin
  if not RegQueryStringValue(HKCU, 'Environment', 'Path', Path) then
    Result := True
  else
    Result := Pos(';' + Uppercase(Dir) + ';', ';' + Uppercase(Path) + ';') = 0;
end;

procedure RemoveFromPath(Dir: String);
var
  Path: String;
begin
  if RegQueryStringValue(HKCU, 'Environment', 'Path', Path) then
  begin
    StringChangeEx(Path, ';' + Dir, '', True);
    StringChangeEx(Path, Dir + ';', '', True);
    if CompareText(Path, Dir) = 0 then
      Path := '';
    RegWriteExpandStringValue(HKCU, 'Environment', 'Path', Path);
  end;
end;

{ Avvio con Windows tolto se, reinstallando, non è più spuntato }
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and not WizardIsTaskSelected('autostart') then
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'GlucoBar');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  { Si chiede PRIMA di rimuovere i file: così è GlucoBar stesso a cancellare
    password (Gestione credenziali), impostazioni e il file della prima versione }
  if (CurUninstallStep = usUninstall) and not UninstallSilent then
    if MsgBox(CustomMessage('RemoveSettings'), mbConfirmation,
              MB_YESNO or MB_DEFBUTTON2) = IDYES then
    begin
      Exec(ExpandConstant('{app}\GlucoBar.exe'), '--forget', '',
           SW_HIDE, ewWaitUntilTerminated, ResultCode);
      { riserva, se l'exe non partisse }
      Exec(ExpandConstant('{sys}\cmdkey.exe'), '/delete:GlucoBar:LibreLinkUp', '',
           SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Exec(ExpandConstant('{sys}\cmdkey.exe'), '/delete:GlucoBar:Dexcom', '',
           SW_HIDE, ewWaitUntilTerminated, ResultCode);
      DelTree(ExpandConstant('{userappdata}\GlucoBar'), True, True, True);
      DeleteFile(ExpandConstant('{%USERPROFILE}\.glicemia_widget.json'));
    end;
  if CurUninstallStep = usPostUninstall then
    RemoveFromPath(ExpandConstant('{app}\bin'));
end;

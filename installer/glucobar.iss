; Installer di GlucoBar (Inno Setup 6)
; Prima servono l'exe e le anteprime:
;   pyinstaller --noconfirm --clean glucobar.spec
;   python tools\previews_to_bmp.py
; Poi: iscc /DAppVersion=0.2.0 installer\glucobar.iss

#ifndef AppVersion
  #define AppVersion "0.2.0"
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
; Stesso nome del mutex creato da glucobar/app.py
AppMutex=GlucoBar
CloseApplications=yes
ShowLanguageDialog=auto

[Languages]
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"; InfoBeforeFile: "disclaimer-it.txt"
Name: "en"; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: "disclaimer-en.txt"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"; InfoBeforeFile: "disclaimer-es.txt"
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"; InfoBeforeFile: "disclaimer-fr.txt"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"; InfoBeforeFile: "disclaimer-de.txt"
Name: "pt"; MessagesFile: "compiler:Languages\Portuguese.isl"; InfoBeforeFile: "disclaimer-pt.txt"

[CustomMessages]
it.ModeTitle=Scegli come vedere la glicemia
it.ModeSubtitle=Potrai cambiarla quando vuoi dall'icona di GlucoBar vicino all'orologio.
it.Name_taskbar=Sulla barra delle applicazioni
it.Name_window=Finestrella
it.Name_desktop=Pannello sullo sfondo
it.Name_tray=Solo icona
it.Desc_taskbar=Valore, freccia e minuti sulla barra, accanto all'orologio. Funziona anche sul secondo monitor e si nasconde con i video a schermo intero.
it.Desc_window=Piccola finestra sempre in primo piano con valore e grafico delle ultime 3 ore. La trascini dove vuoi.
it.Desc_desktop=Pannello sul desktop, dietro le finestre: grafico grande fino a 12 ore, media, minimo, massimo e tempo nel range. Ridimensionabile.
it.Desc_tray=Solo il numero colorato nell'icona vicino all'orologio. Passandoci sopra col mouse vedi freccia e minuti.
it.TaskAutostart=Avvia GlucoBar all'accensione del PC
it.GroupStartup=Avvio:
it.LaunchNow=Avvia GlucoBar adesso
it.RemoveSettings=Vuoi eliminare anche le impostazioni e la password LibreLinkUp salvata su questo PC?
en.ModeTitle=Choose how to see your glucose
en.ModeSubtitle=You can change it at any time from the GlucoBar icon next to the clock.
en.Name_taskbar=On the taskbar
en.Name_window=Small window
en.Name_desktop=Desktop panel
en.Name_tray=Icon only
en.Desc_taskbar=Value, arrow and minutes on the taskbar, next to the clock. Works on a second monitor too and hides during full-screen videos.
en.Desc_window=Small always-on-top window with the value and a 3-hour chart. Drag it anywhere.
en.Desc_desktop=Panel on the desktop, behind your windows: large chart up to 12 hours, average, min, max and time in range. Resizable.
en.Desc_tray=Just the colored number in the icon next to the clock. Hover it to see the arrow and minutes.
en.TaskAutostart=Start GlucoBar when Windows starts
en.GroupStartup=Startup:
en.LaunchNow=Start GlucoBar now
en.RemoveSettings=Do you also want to delete the settings and the LibreLinkUp password saved on this PC?
es.ModeTitle=Elige cómo ver tu glucosa
es.ModeSubtitle=Podrás cambiarlo cuando quieras desde el icono de GlucoBar junto al reloj.
es.Name_taskbar=En la barra de tareas
es.Name_window=Ventana pequeña
es.Name_desktop=Panel en el escritorio
es.Name_tray=Solo icono
es.Desc_taskbar=Valor, flecha y minutos en la barra, junto al reloj. Funciona también en un segundo monitor y se oculta con vídeos a pantalla completa.
es.Desc_window=Ventana pequeña siempre visible con el valor y un gráfico de 3 horas. Arrástrala donde quieras.
es.Desc_desktop=Panel en el escritorio, detrás de las ventanas: gráfico grande de hasta 12 horas, media, mínimo, máximo y tiempo en rango. Redimensionable.
es.Desc_tray=Solo el número en color en el icono junto al reloj. Pasa el ratón por encima para ver la flecha y los minutos.
es.TaskAutostart=Iniciar GlucoBar al encender el PC
es.GroupStartup=Inicio:
es.LaunchNow=Iniciar GlucoBar ahora
es.RemoveSettings=¿Quieres borrar también los ajustes y la contraseña de LibreLinkUp guardada en este PC?
fr.ModeTitle=Choisissez comment voir votre glycémie
fr.ModeSubtitle=Vous pourrez le changer à tout moment depuis l'icône GlucoBar près de l'horloge.
fr.Name_taskbar=Sur la barre des tâches
fr.Name_window=Petite fenêtre
fr.Name_desktop=Panneau sur le bureau
fr.Name_tray=Icône seule
fr.Desc_taskbar=Valeur, flèche et minutes sur la barre, près de l'horloge. Fonctionne aussi sur un second écran et se masque pendant les vidéos plein écran.
fr.Desc_window=Petite fenêtre toujours au premier plan avec la valeur et un graphique de 3 heures. Déplacez-la où vous voulez.
fr.Desc_desktop=Panneau sur le bureau, derrière les fenêtres : grand graphique jusqu'à 12 heures, moyenne, min, max et temps dans la cible. Redimensionnable.
fr.Desc_tray=Seulement le chiffre en couleur dans l'icône près de l'horloge. Survolez-la pour voir la flèche et les minutes.
fr.TaskAutostart=Lancer GlucoBar au démarrage de Windows
fr.GroupStartup=Démarrage :
fr.LaunchNow=Lancer GlucoBar maintenant
fr.RemoveSettings=Voulez-vous aussi supprimer les réglages et le mot de passe LibreLinkUp enregistré sur ce PC ?
de.ModeTitle=Wähle, wie du deinen Glukosewert siehst
de.ModeSubtitle=Du kannst es jederzeit über das GlucoBar-Symbol neben der Uhr ändern.
de.Name_taskbar=Auf der Taskleiste
de.Name_window=Kleines Fenster
de.Name_desktop=Desktop-Panel
de.Name_tray=Nur Symbol
de.Desc_taskbar=Wert, Pfeil und Minuten auf der Taskleiste neben der Uhr. Funktioniert auch auf einem zweiten Monitor und verschwindet bei Vollbild-Videos.
de.Desc_window=Kleines Fenster immer im Vordergrund mit Wert und 3-Stunden-Grafik. Frei verschiebbar.
de.Desc_desktop=Panel auf dem Desktop hinter den Fenstern: große Grafik bis 12 Stunden, Mittelwert, Min, Max und Zeit im Zielbereich. Größe veränderbar.
de.Desc_tray=Nur die farbige Zahl im Symbol neben der Uhr. Mit der Maus darüber siehst du Pfeil und Minuten.
de.TaskAutostart=GlucoBar beim Start von Windows öffnen
de.GroupStartup=Start:
de.LaunchNow=GlucoBar jetzt starten
de.RemoveSettings=Sollen auch die Einstellungen und das auf diesem PC gespeicherte LibreLinkUp-Passwort gelöscht werden?
pt.ModeTitle=Escolha como ver a sua glicose
pt.ModeSubtitle=Pode mudar quando quiser no ícone do GlucoBar junto ao relógio.
pt.Name_taskbar=Na barra de tarefas
pt.Name_window=Janela pequena
pt.Name_desktop=Painel no ambiente de trabalho
pt.Name_tray=Só ícone
pt.Desc_taskbar=Valor, seta e minutos na barra, junto ao relógio. Funciona também num segundo monitor e esconde-se durante vídeos em ecrã inteiro.
pt.Desc_window=Janela pequena sempre visível com o valor e um gráfico de 3 horas. Arraste-a para onde quiser.
pt.Desc_desktop=Painel no ambiente de trabalho, atrás das janelas: gráfico grande até 12 horas, média, mínimo, máximo e tempo no alvo. Redimensionável.
pt.Desc_tray=Apenas o número colorido no ícone junto ao relógio. Passe o rato por cima para ver a seta e os minutos.
pt.TaskAutostart=Iniciar o GlucoBar ao ligar o PC
pt.GroupStartup=Arranque:
pt.LaunchNow=Iniciar o GlucoBar agora
pt.RemoveSettings=Quer apagar também as definições e a palavra-passe LibreLinkUp guardada neste PC?

[Tasks]
Name: "autostart"; Description: "{cm:TaskAutostart}"; GroupDescription: "{cm:GroupStartup}"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\GlucoBar\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; anteprime della pagina "Scegli la modalità" (non vengono installate)
Source: "build\previews\*.bmp"; Flags: dontcopy

[InstallDelete]
; collegamenti della 0.1.0, che aveva un collegamento per modalità
Type: files; Name: "{group}\GlucoBar - *.lnk"
Type: files; Name: "{userstartup}\GlucoBar - *.lnk"
Type: files; Name: "{autodesktop}\GlucoBar - *.lnk"

[Icons]
Name: "{group}\GlucoBar"; Filename: "{app}\GlucoBar.exe"
Name: "{group}\{cm:UninstallProgram,GlucoBar}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\GlucoBar"; Filename: "{app}\GlucoBar.exe"; Tasks: desktopicon
Name: "{userstartup}\GlucoBar"; Filename: "{app}\GlucoBar.exe"; Tasks: autostart

[Run]
; salva modalità e lingua scelte (anche se GlucoBar non viene avviato subito)
Filename: "{app}\GlucoBar.exe"; Parameters: "--set-mode {code:SelectedMode} --set-language {language}"; Flags: runhidden waituntilterminated
Filename: "{app}\GlucoBar.exe"; Description: "{cm:LaunchNow}"; Flags: nowait postinstall skipifsilent

[Code]
var
  ModePage: TWizardPage;
  ModeButtons: array of TNewRadioButton;
  ModePreview: TBitmapImage;
  ModeDescription: TNewStaticText;

function ModeId(I: Integer): String;
begin
  case I of
    0: Result := 'taskbar';
    1: Result := 'window';
    2: Result := 'desktop';
  else
    Result := 'tray';
  end;
end;

{ Anteprima nella lingua dell'installazione, es. it_taskbar.bmp }
function PreviewFile(I: Integer): String;
begin
  Result := ActiveLanguage + '_' + ModeId(I) + '.bmp';
end;

procedure ModeClick(Sender: TObject);
var
  I: Integer;
begin
  for I := 0 to 3 do
    if ModeButtons[I].Checked then
    begin
      ModePreview.Bitmap.LoadFromFile(ExpandConstant('{tmp}\') + PreviewFile(I));
      ModeDescription.Caption := CustomMessage('Desc_' + ModeId(I));
    end;
end;

procedure InitializeWizard;
var
  I, ListWidth, Gap: Integer;
begin
  ModePage := CreateCustomPage(wpInfoBefore, CustomMessage('ModeTitle'),
                               CustomMessage('ModeSubtitle'));
  ListWidth := ScaleX(160);
  Gap := ScaleX(12);

  SetArrayLength(ModeButtons, 4);
  for I := 0 to 3 do
  begin
    ExtractTemporaryFile(PreviewFile(I));
    ModeButtons[I] := TNewRadioButton.Create(ModePage);
    ModeButtons[I].Parent := ModePage.Surface;
    ModeButtons[I].Caption := CustomMessage('Name_' + ModeId(I));
    ModeButtons[I].Left := 0;
    ModeButtons[I].Top := ScaleY(4) + I * ScaleY(26);
    ModeButtons[I].Width := ListWidth;
    ModeButtons[I].OnClick := @ModeClick;
  end;

  ModePreview := TBitmapImage.Create(ModePage);
  ModePreview.Parent := ModePage.Surface;
  ModePreview.Left := ListWidth + Gap;
  ModePreview.Top := 0;
  ModePreview.Width := ModePage.SurfaceWidth - ListWidth - Gap;
  ModePreview.Height := ModePreview.Width * 200 div 320;
  if ModePreview.Height > ModePage.SurfaceHeight then
  begin
    ModePreview.Height := ModePage.SurfaceHeight;
    ModePreview.Width := ModePreview.Height * 320 div 200;
  end;
  ModePreview.Stretch := True;

  ModeDescription := TNewStaticText.Create(ModePage);
  ModeDescription.Parent := ModePage.Surface;
  ModeDescription.Left := 0;
  ModeDescription.Top := ScaleY(4) + 4 * ScaleY(26) + ScaleY(8);
  ModeDescription.AutoSize := False;
  ModeDescription.WordWrap := True;
  ModeDescription.Width := ListWidth;
  ModeDescription.Height := ModePage.SurfaceHeight - ModeDescription.Top;

  ModeButtons[0].Checked := True;
  ModeClick(nil);
end;

{ Usata da [Run]: la modalità scelta nella pagina }
function SelectedMode(Param: String): String;
var
  I: Integer;
begin
  Result := 'taskbar';
  for I := 0 to 3 do
    if ModeButtons[I].Checked then
      Result := ModeId(I);
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

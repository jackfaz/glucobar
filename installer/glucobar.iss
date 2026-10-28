; Installer di GlucoBar (Inno Setup 6)
; Prima servono l'exe e le anteprime:
;   pyinstaller --noconfirm --clean glucobar.spec
;   python tools\previews_to_bmp.py
; Poi: iscc /DAppVersion=0.9.4 installer\glucobar.iss
; Installazione silenziosa con scelte: /VERYSILENT /ELEMENTS=desktop,tray /SENSOR=dexcom /LANG=it

#ifndef AppVersion
  #define AppVersion "0.9.4"
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
; Niente AppMutex: invece di chiedere all'utente di chiudere GlucoBar, l'installer e la
; disinstallazione lo chiudono da soli (vedi CloseGlucoBar più sotto).
; Niente Gestione riavvio di Windows: GlucoBar lo chiude CloseGlucoBar, che poi lo riapre
CloseApplications=no
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
it.RemoveSettings=Vuoi eliminare anche le impostazioni e le password e i token (LibreLinkUp, Dexcom, Nightscout) salvati su questo PC?
it.NeedOne=Scegli almeno un elemento da mostrare.
it.PreviewHint=Spunta cosa vuoi vedere: l'anteprima mostra la tua combinazione.
it.SensorTitle=Quale sensore usi?
it.SensorSubtitle=GlucoBar legge la glicemia dal servizio di condivisione del sensore: va attivato una volta sola, dal telefono.
it.Sensor_libre=FreeStyle Libre (tramite LibreLinkUp)
it.Sensor_dexcom=Dexcom G6, G7, ONE+ (tramite Dexcom Share) · beta
it.Steps_libre=1. Nell'app LibreLink apri il menu e tocca «App connesse».%n2. Accanto a LibreLinkUp tocca «Gestisci», poi «Aggiungi collegamento».%n3. Inserisci il tuo nome e l'email del tuo account LibreLink, poi invia l'invito.%n4. Installa l'app LibreLinkUp, tocca «Accedi» e usa la stessa email e la stessa password di LibreLink. Accetta l'invito e i termini d'uso.%n5. Al primo avvio di GlucoBar inserisci la stessa email e la stessa password.%n%nDopo puoi disinstallare LibreLinkUp dal telefono.
it.Steps_dexcom=1. Nell'app Dexcom attiva la condivisione (Share) e invita almeno un follower.%n2. Al primo avvio di GlucoBar inserisci il tuo account Dexcom (email, telefono con prefisso o nome utente) e la password.%n3. Indica dove hai creato l'account: dall'Italia è «Fuori dagli Stati Uniti».%n%nIl supporto Dexcom è nuovo: se qualcosa non funziona, faccelo sapere su GitHub.
it.GuideLink=Guida con le immagini
it.GuideUrl_libre=/blob/main/README.it.md#configurare-librelinkup
it.GuideUrl_dexcom=/blob/main/README.it.md#installazione
it.Sensor_nightscout=Nightscout o Nocturne (qualsiasi sensore collegato al tuo sito) · beta
it.Steps_nightscout=1. Ti serve un sito Nightscout o Nocturne che riceve già le letture del sensore (da xDrip+, Juggluco, AndroidAPS, Loop, Medtronic, Eversense…).%n2. Se il sito non è pubblico, crea un token in sola lettura.%n   Nightscout: Admin Tools → nuovo soggetto con ruolo «readable», poi copia il token.%n   Nocturne: Settings → Connectors → API tokens → Create API token, con il permesso di lettura «Blood glucose».%n3. Al primo avvio di GlucoBar inserisci l'indirizzo del sito, quello che apri nel browser (es. https://mionome.herokuapp.com), e il token, oppure lascialo vuoto se il sito è pubblico.%n%nIl supporto Nightscout e Nocturne è nuovo: se qualcosa non funziona, faccelo sapere su GitHub.
it.GuideUrl_nightscout=/blob/main/README.it.md#installazione
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
en.RemoveSettings=Do you also want to delete the settings and the passwords and tokens (LibreLinkUp, Dexcom, Nightscout) saved on this PC?
en.NeedOne=Please choose at least one thing to show.
en.PreviewHint=Tick what you want to see: the preview shows your combination.
en.SensorTitle=Which sensor do you use?
en.SensorSubtitle=GlucoBar reads your glucose from the sensor maker's sharing service: you turn it on once, on your phone.
en.Sensor_libre=FreeStyle Libre (via LibreLinkUp)
en.Sensor_dexcom=Dexcom G6, G7, ONE+ (via Dexcom Share) · beta
en.Steps_libre=1. In the LibreLink app, open the menu and tap "Connected Apps".%n2. Next to LibreLinkUp, tap "Manage", then "Add Connection".%n3. Enter your name and the email of your LibreLink account, then send the invitation.%n4. Install the LibreLinkUp app, tap "Log In" and use the same email and password as LibreLink. Accept the invitation and the terms of use.%n5. When GlucoBar starts for the first time, enter the same email and password.%n%nYou can uninstall LibreLinkUp from your phone afterwards.
en.Steps_dexcom=1. In the Dexcom app, turn on Share and invite at least one follower.%n2. When GlucoBar starts for the first time, enter your Dexcom account (email, phone number with country code or user name) and password.%n3. Choose where the account was created: in Europe it is "Outside the United States".%n%nDexcom support is new: if something does not work, please tell us on GitHub.
en.GuideLink=Guide with pictures
en.GuideUrl_libre=#setting-up-librelinkup
en.GuideUrl_dexcom=#install
en.Sensor_nightscout=Nightscout or Nocturne (any sensor that uploads to your site) · beta
en.Steps_nightscout=1. You need a Nightscout or Nocturne site that already receives your sensor readings (from xDrip+, Juggluco, AndroidAPS, Loop, Medtronic, Eversense…).%n2. If the site is not public, create a read-only token.%n   Nightscout: Admin Tools → add a new subject with the "readable" role, then copy its token.%n   Nocturne: Settings → Connectors → API tokens → Create API token, with read permission for "Blood glucose".%n3. When GlucoBar starts for the first time, enter the site address, the one you open in the browser (e.g. https://yourname.herokuapp.com), and the token, or leave the token empty if the site is public.%n%nNightscout and Nocturne support is new: if something does not work, please tell us on GitHub.
en.GuideUrl_nightscout=#install
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
es.RemoveSettings=¿Quieres borrar también los ajustes y las contraseñas y tokens (LibreLinkUp, Dexcom, Nightscout) guardados en este PC?
es.NeedOne=Elige al menos un elemento para mostrar.
es.PreviewHint=Marca lo que quieres ver: la vista previa muestra tu combinación.
es.SensorTitle=¿Qué sensor usas?
es.SensorSubtitle=GlucoBar lee la glucosa del servicio para compartir datos del fabricante: se activa una sola vez, desde el móvil.
es.Sensor_libre=FreeStyle Libre (a través de LibreLinkUp)
es.Sensor_dexcom=Dexcom G6, G7, ONE+ (a través de Dexcom Share) · beta
es.Steps_libre=1. En la app LibreLink abre el menú y toca «Aplicaciones conectadas».%n2. Junto a LibreLinkUp toca «Gestionar» y luego «Añadir conexión».%n3. Escribe tu nombre y el email de tu cuenta LibreLink y envía la invitación.%n4. Instala la app LibreLinkUp, toca «Iniciar sesión» y usa el mismo email y la misma contraseña que en LibreLink. Acepta la invitación y los términos de uso.%n5. La primera vez que se abra GlucoBar, escribe el mismo email y la misma contraseña.%n%nDespués puedes desinstalar LibreLinkUp del móvil.
es.Steps_dexcom=1. En la app Dexcom activa Compartir e invita al menos a un seguidor.%n2. La primera vez que se abra GlucoBar, escribe tu cuenta Dexcom (email, teléfono con prefijo o nombre de usuario) y la contraseña.%n3. Elige dónde creaste la cuenta: en Europa es «Fuera de Estados Unidos».%n%nEl soporte de Dexcom es nuevo: si algo no funciona, cuéntanoslo en GitHub.
es.GuideLink=Guía con imágenes (en inglés)
es.GuideUrl_libre=#setting-up-librelinkup
es.GuideUrl_dexcom=#install
es.Sensor_nightscout=Nightscout o Nocturne (cualquier sensor que suba datos a tu sitio) · beta
es.Steps_nightscout=1. Necesitas un sitio Nightscout o Nocturne que ya reciba las lecturas de tu sensor (desde xDrip+, Juggluco, AndroidAPS, Loop, Medtronic, Eversense…).%n2. Si el sitio no es público, crea un token de solo lectura.%n   Nightscout: Admin Tools → añade un nuevo sujeto con el rol «readable» y copia su token.%n   Nocturne: Settings → Connectors → API tokens → Create API token, con permiso de lectura para «Blood glucose».%n3. La primera vez que se abra GlucoBar, escribe la dirección del sitio, la que abres en el navegador (p. ej. https://tunombre.herokuapp.com), y el token, o déjalo vacío si el sitio es público.%n%nEl soporte de Nightscout y Nocturne es nuevo: si algo no funciona, cuéntanoslo en GitHub.
es.GuideUrl_nightscout=#install
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
fr.RemoveSettings=Voulez-vous aussi supprimer les réglages et les mots de passe et jetons (LibreLinkUp, Dexcom, Nightscout) enregistrés sur ce PC ?
fr.NeedOne=Choisissez au moins un élément à afficher.
fr.PreviewHint=Cochez ce que vous voulez voir : l'aperçu montre votre combinaison.
fr.SensorTitle=Quel capteur utilisez-vous ?
fr.SensorSubtitle=GlucoBar lit la glycémie depuis le service de partage du fabricant : il s'active une seule fois, depuis le téléphone.
fr.Sensor_libre=FreeStyle Libre (via LibreLinkUp)
fr.Sensor_dexcom=Dexcom G6, G7, ONE+ (via Dexcom Share) · bêta
fr.Steps_libre=1. Dans l'app LibreLink, ouvrez le menu et touchez « Applications connectées ».%n2. À côté de LibreLinkUp, touchez « Gérer », puis « Ajouter une connexion ».%n3. Saisissez votre nom et l'e-mail de votre compte LibreLink, puis envoyez l'invitation.%n4. Installez l'app LibreLinkUp, touchez « Se connecter » et utilisez le même e-mail et le même mot de passe que LibreLink. Acceptez l'invitation et les conditions d'utilisation.%n5. Au premier lancement de GlucoBar, saisissez le même e-mail et le même mot de passe.%n%nVous pouvez ensuite désinstaller LibreLinkUp du téléphone.
fr.Steps_dexcom=1. Dans l'app Dexcom, activez le Partage et invitez au moins un abonné.%n2. Au premier lancement de GlucoBar, saisissez votre compte Dexcom (e-mail, téléphone avec indicatif ou nom d'utilisateur) et le mot de passe.%n3. Indiquez où le compte a été créé : en Europe, c'est « Hors des États-Unis ».%n%nLa prise en charge de Dexcom est nouvelle : si quelque chose ne fonctionne pas, dites-le-nous sur GitHub.
fr.GuideLink=Guide en images (en anglais)
fr.GuideUrl_libre=#setting-up-librelinkup
fr.GuideUrl_dexcom=#install
fr.Sensor_nightscout=Nightscout ou Nocturne (tout capteur envoyé vers votre site) · bêta
fr.Steps_nightscout=1. Il vous faut un site Nightscout ou Nocturne qui reçoit déjà les mesures de votre capteur (depuis xDrip+, Juggluco, AndroidAPS, Loop, Medtronic, Eversense…).%n2. Si le site n'est pas public, créez un jeton en lecture seule.%n   Nightscout : Admin Tools → ajoutez un nouveau sujet avec le rôle « readable », puis copiez son jeton.%n   Nocturne : Settings → Connectors → API tokens → Create API token, avec la permission de lecture « Blood glucose ».%n3. Au premier lancement de GlucoBar, saisissez l'adresse du site, celle que vous ouvrez dans le navigateur (par ex. https://votrenom.herokuapp.com), et le jeton, ou laissez-le vide si le site est public.%n%nLa prise en charge de Nightscout et Nocturne est nouvelle : si quelque chose ne fonctionne pas, dites-le-nous sur GitHub.
fr.GuideUrl_nightscout=#install
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
de.RemoveSettings=Sollen auch die Einstellungen und die auf diesem PC gespeicherten Passwörter und Tokens (LibreLinkUp, Dexcom, Nightscout) gelöscht werden?
de.NeedOne=Bitte wähle mindestens ein Element aus.
de.PreviewHint=Kreuze an, was du sehen möchtest: die Vorschau zeigt deine Auswahl.
de.SensorTitle=Welchen Sensor verwendest du?
de.SensorSubtitle=GlucoBar liest den Glukosewert über den Teilen-Dienst des Herstellers: Du aktivierst ihn einmal auf dem Handy.
de.Sensor_libre=FreeStyle Libre (über LibreLinkUp)
de.Sensor_dexcom=Dexcom G6, G7, ONE+ (über Dexcom Share) · Beta
de.Steps_libre=1. Öffne in der LibreLink-App das Menü und tippe auf „Verbundene Apps“.%n2. Tippe neben LibreLinkUp auf „Verwalten“, dann auf „Verbindung hinzufügen“.%n3. Gib deinen Namen und die E-Mail deines LibreLink-Kontos ein und sende die Einladung.%n4. Installiere die LibreLinkUp-App, tippe auf „Anmelden“ und verwende dieselbe E-Mail und dasselbe Passwort wie bei LibreLink. Nimm die Einladung und die Nutzungsbedingungen an.%n5. Gib beim ersten Start von GlucoBar dieselbe E-Mail und dasselbe Passwort ein.%n%nDanach kannst du LibreLinkUp vom Handy deinstallieren.
de.Steps_dexcom=1. Aktiviere in der Dexcom-App die Freigabe (Share) und lade mindestens einen Follower ein.%n2. Gib beim ersten Start von GlucoBar dein Dexcom-Konto (E-Mail, Telefonnummer mit Landesvorwahl oder Benutzername) und das Passwort ein.%n3. Wähle, wo das Konto erstellt wurde: in Europa ist das „Außerhalb der USA“.%n%nDie Dexcom-Unterstützung ist neu: Wenn etwas nicht funktioniert, sag uns bitte auf GitHub Bescheid.
de.GuideLink=Anleitung mit Bildern (auf Englisch)
de.GuideUrl_libre=#setting-up-librelinkup
de.GuideUrl_dexcom=#install
de.Sensor_nightscout=Nightscout oder Nocturne (jeder Sensor, der zu deiner Seite hochlädt) · Beta
de.Steps_nightscout=1. Du brauchst eine Nightscout- oder Nocturne-Seite, die deine Sensorwerte bereits empfängt (von xDrip+, Juggluco, AndroidAPS, Loop, Medtronic, Eversense…).%n2. Wenn die Seite nicht öffentlich ist, erstelle ein Token nur zum Lesen.%n   Nightscout: Admin Tools → neues Subjekt mit der Rolle „readable“ hinzufügen und sein Token kopieren.%n   Nocturne: Settings → Connectors → API tokens → Create API token, mit Leserecht für „Blood glucose“.%n3. Gib beim ersten Start von GlucoBar die Adresse der Seite ein, die du im Browser öffnest (z. B. https://deinname.herokuapp.com), und das Token, oder lass es leer, wenn die Seite öffentlich ist.%n%nDie Unterstützung für Nightscout und Nocturne ist neu: Wenn etwas nicht funktioniert, sag uns bitte auf GitHub Bescheid.
de.GuideUrl_nightscout=#install
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
pt.RemoveSettings=Quer apagar também as definições e as palavras-passe e tokens (LibreLinkUp, Dexcom, Nightscout) guardados neste PC?
pt.NeedOne=Escolha pelo menos um elemento para mostrar.
pt.PreviewHint=Marque o que quer ver: a pré-visualização mostra a sua combinação.
pt.SensorTitle=Que sensor utiliza?
pt.SensorSubtitle=O GlucoBar lê a glicose a partir do serviço de partilha do fabricante: ativa-se uma só vez, no telemóvel.
pt.Sensor_libre=FreeStyle Libre (através do LibreLinkUp)
pt.Sensor_dexcom=Dexcom G6, G7, ONE+ (através do Dexcom Share) · beta
pt.Steps_libre=1. Na app LibreLink abra o menu e toque em «Aplicações ligadas».%n2. Ao lado de LibreLinkUp toque em «Gerir» e depois em «Adicionar ligação».%n3. Introduza o seu nome e o email da sua conta LibreLink e envie o convite.%n4. Instale a app LibreLinkUp, toque em «Iniciar sessão» e use o mesmo email e a mesma palavra-passe do LibreLink. Aceite o convite e os termos de utilização.%n5. Na primeira vez que o GlucoBar abrir, introduza o mesmo email e a mesma palavra-passe.%n%nDepois pode desinstalar o LibreLinkUp do telemóvel.
pt.Steps_dexcom=1. Na app Dexcom ative a Partilha e convide pelo menos um seguidor.%n2. Na primeira vez que o GlucoBar abrir, introduza a sua conta Dexcom (email, telemóvel com indicativo ou nome de utilizador) e a palavra-passe.%n3. Escolha onde criou a conta: na Europa é «Fora dos Estados Unidos».%n%nO suporte Dexcom é novo: se algo não funcionar, diga-nos no GitHub.
pt.GuideLink=Guia com imagens (em inglês)
pt.GuideUrl_libre=#setting-up-librelinkup
pt.GuideUrl_dexcom=#install
pt.Sensor_nightscout=Nightscout ou Nocturne (qualquer sensor que envie dados para o seu site) · beta
pt.Steps_nightscout=1. Precisa de um site Nightscout ou Nocturne que já receba as leituras do seu sensor (do xDrip+, Juggluco, AndroidAPS, Loop, Medtronic, Eversense…).%n2. Se o site não for público, crie um token só de leitura.%n   Nightscout: Admin Tools → adicione um novo sujeito com a função «readable» e copie o token.%n   Nocturne: Settings → Connectors → API tokens → Create API token, com permissão de leitura para «Blood glucose».%n3. Na primeira vez que o GlucoBar abrir, introduza o endereço do site, o que abre no navegador (ex. https://onome.herokuapp.com), e o token, ou deixe-o vazio se o site for público.%n%nO suporte Nightscout e Nocturne é novo: se algo não funcionar, diga-nos no GitHub.
pt.GuideUrl_nightscout=#install

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
; salva elementi, lingua e sensore scelti (anche se GlucoBar non viene avviato subito).
; In un aggiornamento silenzioso (winget) solo quelli passati da riga di comando:
; le scelte fatte nell'app restano
Filename: "{app}\GlucoBar.exe"; Parameters: "{code:ChoiceArgs}"; Flags: runhidden waituntilterminated; Check: HasChoices
Filename: "{app}\GlucoBar.exe"; Description: "{cm:LaunchNow}"; Flags: nowait postinstall skipifsilent
; aggiornamento silenzioso (es. winget): riapre GlucoBar se era aperto
Filename: "{app}\GlucoBar.exe"; Flags: nowait; Check: ReopenAfterSilentUpdate

[Code]
var
  ModePage: TWizardPage;
  ModeBoxes: array of TNewCheckBox;
  ModePreview: TBitmapImage;          // il desktop vuoto
  ModeLayers: array of TBitmapImage;  // un ritaglio per elemento, sopra la base
  ModeDescription: TNewStaticText;
  LastClicked: Integer;
  WasRunning: Boolean;   // GlucoBar era aperto ed è stato chiuso per installare
  SensorPage: TWizardPage;
  SensorRadios: array of TNewRadioButton;
  SensorSteps: TNewMemo;
  SensorLink: TNewStaticText;

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

{ ---- pagina "Quale sensore usi?": istruzioni per il sensore scelto ---- }

{ Stesso ordine di SOURCES in glucobar/sources.py }
function SensorId(I: Integer): String;
begin
  case I of
    1: Result := 'dexcom';
    2: Result := 'nightscout';
  else
    Result := 'libre';
  end;
end;

function SelectedSensor: Integer;
var
  I: Integer;
begin
  Result := 0;
  for I := 1 to GetArrayLength(SensorRadios) - 1 do
    if SensorRadios[I].Checked then
      Result := I;
end;

procedure UpdateSensor;
begin
  if SensorSteps = nil then
    Exit;
  SensorSteps.Text := CustomMessage('Steps_' + SensorId(SelectedSensor));
end;

procedure SensorClick(Sender: TObject);
begin
  UpdateSensor;
end;

procedure GuideClick(Sender: TObject);
var
  ErrorCode: Integer;
begin
  ShellExec('open', '{#RepoUrl}' + CustomMessage('GuideUrl_' + SensorId(SelectedSensor)),
            '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
end;

{ Reinstallando, propone il sensore già configurato }
function ConfiguredSensor: Integer;
var
  Config: AnsiString;
begin
  Result := 0;
  if LoadStringFromFile(ExpandConstant('{userappdata}\GlucoBar\config.json'), Config) then
    if Pos('"source": "dexcom"', Config) > 0 then
      Result := 1
    else if Pos('"source": "nightscout"', Config) > 0 then
      Result := 2;
end;

{ Elementi scelti nell'installazione attuale, es. ",taskbar,tray," ('' se non c'è) }
function ConfiguredElements: String;
var
  Config: AnsiString;
  Start, Stop: Integer;
  List: String;
begin
  Result := '';
  if not LoadStringFromFile(ExpandConstant('{userappdata}\GlucoBar\config.json'), Config) then
    Exit;
  Start := Pos('"elements": [', Config);
  if Start = 0 then
    Exit;
  List := Copy(Config, Start + 13, 200);
  Stop := Pos(']', List);
  if Stop > 0 then
    List := Copy(List, 1, Stop);
  Result := ',';
  if Pos('"taskbar"', List) > 0 then Result := Result + 'taskbar,';
  if Pos('"tray"', List) > 0 then Result := Result + 'tray,';
  if Pos('"window"', List) > 0 then Result := Result + 'window,';
  if Pos('"desktop"', List) > 0 then Result := Result + 'desktop,';
  if Result = ',' then
    Result := '';
end;

procedure CreateSensorPage(After: Integer);
var
  I, Row, Wanted: Integer;
  Param: String;
begin
  SensorPage := CreateCustomPage(After, CustomMessage('SensorTitle'),
                                 CustomMessage('SensorSubtitle'));
  Row := ScaleY(22);
  SetArrayLength(SensorRadios, 3);
  for I := 0 to 2 do
  begin
    SensorRadios[I] := TNewRadioButton.Create(SensorPage);
    SensorRadios[I].Parent := SensorPage.Surface;
    SensorRadios[I].Caption := CustomMessage('Sensor_' + SensorId(I));
    SensorRadios[I].Left := 0;
    SensorRadios[I].Top := I * Row;
    SensorRadios[I].Width := SensorPage.SurfaceWidth;
  end;

  SensorLink := TNewStaticText.Create(SensorPage);
  SensorLink.Parent := SensorPage.Surface;
  SensorLink.Caption := CustomMessage('GuideLink');
  SensorLink.Font.Color := clBlue;
  SensorLink.Font.Style := [fsUnderline];
  SensorLink.Cursor := crHand;
  SensorLink.OnClick := @GuideClick;
  SensorLink.Left := 0;
  SensorLink.Top := SensorPage.SurfaceHeight - SensorLink.Height;

  SensorSteps := TNewMemo.Create(SensorPage);
  SensorSteps.Parent := SensorPage.Surface;
  SensorSteps.Left := 0;
  SensorSteps.Top := 3 * Row + ScaleY(6);
  SensorSteps.Width := SensorPage.SurfaceWidth;
  SensorSteps.Height := SensorLink.Top - SensorSteps.Top - ScaleY(6);
  SensorSteps.ReadOnly := True;
  SensorSteps.WordWrap := True;
  SensorSteps.ScrollBars := ssVertical;

  { da riga di comando (anche winget): /SENSOR=libre, dexcom o nightscout }
  Param := Lowercase(ExpandConstant('{param:SENSOR|}'));
  if Param = 'dexcom' then
    Wanted := 1
  else if Param = 'nightscout' then
    Wanted := 2
  else if Param = 'libre' then
    Wanted := 0
  else
    Wanted := ConfiguredSensor;
  SensorRadios[Wanted].Checked := True;
  { i clic solo ora: il memo esiste già }
  for I := 0 to 2 do
    SensorRadios[I].OnClick := @SensorClick;
  UpdateSensor;
end;

{ Usata da [Run]: "libre", "dexcom" o "nightscout" }
function SelectedSource(Param: String): String;
begin
  Result := SensorId(SelectedSensor);
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

  { Prima installazione: nessuna casella spuntata, si sceglie guardando l'anteprima.
    Aggiornamento: le scelte di adesso. Da riga di comando (anche winget):
    /ELEMENTS=desktop,tray }
  Elements := Lowercase(ExpandConstant('{param:ELEMENTS|}'));
  if Elements <> '' then
    Elements := ',' + Elements + ','
  else
    Elements := ConfiguredElements;
  if Elements <> '' then
    for I := 0 to 3 do
      ModeBoxes[I].Checked := Pos(',' + ModeId(I) + ',', Elements) > 0;
  UpdatePreview;

  CreateSensorPage(ModePage.ID);
end;

{ Almeno un elemento da mostrare }
function NextButtonClick(CurPageID: Integer): Boolean;
var
  I: Integer;
begin
  Result := True;
  { in silenzio nessuno può rispondere a un messaggio: senza /ELEMENTS restano le
    scelte di prima (0.8.x: l'aggiornamento silenzioso restava fermo qui per sempre) }
  if (CurPageID = ModePage.ID) and not WizardSilent then
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

{ Usata da [Run]: le scelte da salvare. Con l'installazione guidata tutte; in quella
  silenziosa solo /ELEMENTS, /LANG e /SENSOR se ci sono (0.8.x: un aggiornamento con
  winget rimetteva barra e icona e la lingua dell'installer) }
function ChoiceArgs(Param: String): String;
begin
  Result := '';
  if (not WizardSilent) or (ExpandConstant('{param:ELEMENTS|}') <> '') then
    Result := Result + ' --set-elements ' + SelectedElements('');
  if (not WizardSilent) or (ExpandConstant('{param:LANG|}') <> '') then
    Result := Result + ' --set-language ' + ExpandConstant('{language}');
  if (not WizardSilent) or (ExpandConstant('{param:SENSOR|}') <> '') then
    Result := Result + ' --set-source ' + SelectedSource('');
  Result := Trim(Result);
end;

function HasChoices: Boolean;
begin
  Result := ChoiceArgs('') <> '';
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

{ GlucoBar aperto: prima gli chiede di chiudersi da solo (l'icona sparisce subito
  dall'orologio), poi, se non risponde (es. una versione senza --quit), lo chiude }
procedure CloseGlucoBar;
var
  ResultCode: Integer;
begin
  if not CheckForMutexes('GlucoBar') then
    Exit;
  WasRunning := True;
  if FileExists(ExpandConstant('{app}\GlucoBar.exe')) then
    Exec(ExpandConstant('{app}\GlucoBar.exe'), '--quit', '', SW_HIDE,
         ewWaitUntilTerminated, ResultCode);
  if CheckForMutexes('GlucoBar') then
  begin
    Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM GlucoBar.exe', '', SW_HIDE,
         ewWaitUntilTerminated, ResultCode);
    Sleep(500);
  end;
end;

{ Installazione o aggiornamento: chiude GlucoBar prima di sostituire i file }
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  CloseGlucoBar;
  Result := '';
end;

{ Usata da [Run] }
function ReopenAfterSilentUpdate: Boolean;
begin
  Result := WizardSilent and WasRunning;
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
  { prima di tutto: GlucoBar aperto bloccherebbe la rimozione dei file }
  if CurUninstallStep = usUninstall then
    CloseGlucoBar;
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
      Exec(ExpandConstant('{sys}\cmdkey.exe'), '/delete:GlucoBar:Nightscout', '',
           SW_HIDE, ewWaitUntilTerminated, ResultCode);
      DelTree(ExpandConstant('{userappdata}\GlucoBar'), True, True, True);
      DeleteFile(ExpandConstant('{%USERPROFILE}\.glicemia_widget.json'));
    end;
  if CurUninstallStep = usPostUninstall then
    RemoveFromPath(ExpandConstant('{app}\bin'));
end;

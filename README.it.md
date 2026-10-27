<p align="center"><img src="docs/banner.png" alt="GlucoBar: la glicemia del FreeStyle Libre sulla barra di Windows"></p>

<p align="center">
  <a href="https://github.com/jackfaz/glucobar/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/jackfaz/glucobar?include_prereleases&label=release&color=3ecf6e"></a>
  <a href="https://github.com/jackfaz/glucobar/releases"><img alt="Downloads" src="https://img.shields.io/github/downloads/jackfaz/glucobar/total?color=3ecf6e"></a>
  <a href="https://github.com/jackfaz/glucobar/actions/workflows/build.yml"><img alt="Build" src="https://img.shields.io/github/actions/workflow/status/jackfaz/glucobar/build.yml?branch=main"></a>
  <img alt="Windows 10/11" src="https://img.shields.io/badge/Windows-10%20%7C%2011-0078d4">
  <img alt="6 languages" src="https://img.shields.io/badge/languages-6-f5a524">
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-lightgrey"></a>
</p>

<p align="center">
  <a href="https://github.com/jackfaz/glucobar/releases/latest"><b>Scarica per Windows</b></a> ·
  <a href="#installazione">Installazione</a> ·
  <a href="#uso">Uso</a> ·
  <a href="#sensori">Sensori</a> ·
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="README.md">English</a>
</p>

GlucoBar mostra la glicemia del tuo FreeStyle Libre o Dexcom sul PC con Windows, così mentre
lavori puoi tenerla d'occhio senza prendere il telefono. Legge l'ultimo valore da LibreLinkUp
(il servizio di condivisione di Abbott) o da Dexcom Share, e lo mostra con la freccia di
tendenza e da quanti minuti è stato misurato.

Puoi vederla in quattro posti, uno o più insieme: sulla barra delle applicazioni accanto
all'orologio, come icona nell'area di notifica, in una finestrella sempre in primo piano o in
un pannello più grande sul desktop, con il grafico delle ultime 12 ore e qualche statistica.
Funziona anche sul secondo monitor e si nasconde quando un video o un gioco è a schermo intero.

La password resta cifrata nel Gestione credenziali di Windows e viene inviata solo ai server
del produttore del sensore. GlucoBar è gratuito, open source (MIT) e disponibile in italiano, inglese,
spagnolo, francese, tedesco e portoghese.

| Sulla barra | Finestrella |
|---|---|
| ![Barra](docs/preview_taskbar.png) | ![Finestrella](docs/preview_window.png) |
| Valore, freccia e minuti accanto all'orologio. | Sempre in primo piano, con il grafico delle ultime 3 ore. La sposti dove vuoi. |
| **Pannello sullo sfondo** | **Icona vicino all'orologio** |
| ![Pannello sullo sfondo](docs/preview_desktop.png) | ![Icona vicino all'orologio](docs/preview_tray.png) |
| Dietro le finestre: grafico delle ultime 3, 6 o 12 ore, media, minimo, massimo, tempo nel range, variazione in 15 minuti e giorno del sensore. Ridimensionabile. | Il numero colorato nell'area di notifica. Passandoci sopra vedi freccia e minuti. |

Colori: verde nel range (70–180 mg/dL), arancione sopra 180, rosso sotto 70 o sopra 250,
grigio se il dato è di più di 15 minuti fa. Le soglie si possono cambiare.

> **GlucoBar non è un dispositivo medico.** Non usarlo per decidere dosi di insulina o per
> trattare un'ipo: fa fede il lettore o l'app ufficiale. Usa un'API non ufficiale che Abbott
> può cambiare in qualsiasi momento.

## Sensori

| Sensore | Letto tramite | Stato |
|---|---|---|
| FreeStyle Libre (Libre 2, Libre 3 e versioni Plus) | LibreLinkUp | Supportato |
| Dexcom G6, G7, ONE+ | Dexcom Share | Beta, cerchiamo chi lo provi |
| Qualsiasi sensore che invia i dati a Nightscout (Medtronic, Eversense, xDrip+, Juggluco, AndroidAPS, …) | Nightscout | Previsto |
| Medtronic Guardian / Simplera | CareLink | In valutazione |

Il supporto Dexcom è nuovo e finora è stato provato solo con un server Dexcom Share
simulato. Se usi un Dexcom, facci sapere se funziona nelle [Discussions](../../discussions)
o in una [issue](../../issues).

Vorresti un altro sensore? [Apri una issue](../../issues) e dicci quale.

## Installazione

1. **Attiva la condivisione sul telefono (una volta sola).**
   - **FreeStyle Libre:** nell'app **LibreLink**: *Condividi → App collegate → LibreLinkUp →
     Aggiungi* e invita un indirizzo email (meglio diverso da quello di LibreLink). Installa
     l'app **LibreLinkUp**, accedi con quell'email, accetta l'invito e i termini d'uso. Dopo
     puoi disinstallare LibreLinkUp.
   - **Dexcom:** nell'app **Dexcom** attiva la **condivisione (Share)** e invita almeno un
     follower. GlucoBar entra con il tuo account Dexcom, non con quello del follower.
2. Scarica `GlucoBar-Setup-x.y.z.exe` dalla pagina [Release](../../releases/latest) e avvialo.
   Non servono permessi di amministratore.
3. Scegli la lingua dell'installazione, spunta cosa mostrare (con le anteprime) e se avviare
   GlucoBar all'accensione del PC.
4. Al primo avvio scegli il sensore e inserisci l'account: l'email **LibreLinkUp** per
   FreeStyle Libre, oppure email, telefono (con prefisso) o nome utente **Dexcom**.

Windows può mostrare *"Windows ha protetto il PC"* perché l'installer non è ancora firmato
digitalmente: clicca *Ulteriori informazioni → Esegui comunque*. Ogni release riporta
l'impronta SHA-256 dell'installer e il link alla sua scansione su VirusTotal, così puoi
controllare il file prima di avviarlo.

## Uso

- **Clic destro su qualsiasi elemento di GlucoBar** (l'icona, il valore sulla barra, la
  finestrella o il pannello): aggiorna, *Mostra* (spunta gli elementi che vuoi), unità, lingua,
  cambia account, esci. **Doppio clic**: aggiorna subito.
- Windows 11 nasconde le icone nuove sotto la freccetta **^**: trascina l'icona di GlucoBar
  sulla barra per tenerla sempre visibile.
- Barra sul secondo monitor: attiva *Impostazioni → Personalizzazione → Barra delle applicazioni →
  Comportamenti della barra delle applicazioni → Mostra la barra delle applicazioni su tutti gli
  schermi*, poi clic destro sul valore → *Sposta sull'altro monitor*.
- Pannello sullo sfondo: trascinalo per spostarlo, trascina l'angolo in basso a destra per
  ridimensionarlo, clic destro per il periodo del grafico e per bloccarlo.

## Terminale

L'installer aggiunge il comando `glucobar` a ogni nuovo terminale:

```text
glucobar setup                 configurazione guidata: ↑/↓ per scegliere, Spazio per spuntare, Invio
glucobar status                glicemia attuale, es. "133 ↘ mg/dL · 2 min fa"
glucobar set unit=mmol/L low=80
glucobar set elements=desktop,tray autostart=true
glucobar get                   tutte le impostazioni
glucobar login                 cambia sensore o account
glucobar start | forget        avvia GlucoBar | cancella password e impostazioni
glucobar report                riepilogo per le segnalazioni, copiato negli appunti
```

Se GlucoBar è aperto, applica le nuove impostazioni entro due secondi.

Installazione silenziosa con le tue scelte (comoda per script e winget):

```text
GlucoBar-Setup-0.5.2.exe /VERYSILENT /ELEMENTS=taskbar,tray /LANG=it
```

## Impostazioni

`%APPDATA%\GlucoBar\config.json`:

| Chiave | Predefinito | Significato |
|---|---|---|
| `source` | `libre` | `libre` (LibreLinkUp) oppure `dexcom` (Dexcom Share) |
| `dexcom_region` | `ous` | Dove è stato creato l'account Dexcom: `ous` (fuori dagli USA), `us`, `jp` |
| `elements` | `["taskbar", "tray"]` | Cosa mostrare, in qualsiasi combinazione: `taskbar`, `tray` (icona vicino all'orologio), `window`, `desktop` |
| `low` / `high` / `very_high` | 70 / 180 / 250 | Soglie in mg/dL |
| `unit` | `mg/dL` | oppure `mmol/L` |
| `stale_minutes` | 15 | Oltre questo il valore diventa grigio |
| `refresh_seconds` | 60 | Ogni quanto leggere il dato |
| `language` | `auto` | `it`, `en`, `es`, `fr`, `de`, `pt` |
| `taskbar_monitor` | 1 | 1 = monitor principale, 2 = secondo, … |
| `taskbar_offset` | 0 | Pixel di spostamento (negativo = a sinistra) |
| `taskbar_bg` | auto | Colore della tua barra, es. `#202020`, se vedi un alone attorno alle cifre |
| `taskbar_transparent` | true | `false` per uno sfondo pieno |
| `desktop_hours` | 12 | Periodo del grafico del pannello: 3, 6 o 12 |
| `desktop_alpha` | 0.92 | Opacità del pannello (1 = pieno) |

Log: `%APPDATA%\GlucoBar\glucobar.log`.

Se usavi la prima versione (script Python con `.glicemia_widget.json`), al primo avvio
GlucoBar importa da solo impostazioni e password. Poi puoi cancellare quel file.

## Privacy

- La password è salvata **cifrata nel Gestione credenziali di Windows** (voci
  `GlucoBar:LibreLinkUp` e `GlucoBar:Dexcom`), mai nel file delle impostazioni.
- GlucoBar comunica **solo con i server del produttore del sensore**: LibreView di Abbott o
  Dexcom Share. Nessuna statistica, nessun altro server.
- La disinstallazione chiede se eliminare anche impostazioni e password (anche il vecchio
  `.glicemia_widget.json`). Puoi farlo anche in qualsiasi momento con `GlucoBar.exe --forget`.

## Firma del codice

Free code signing provided by [SignPath.io](https://signpath.io), certificate by
[SignPath Foundation](https://signpath.org): la firma digitale è offerta gratuitamente da
SignPath.io, con un certificato di SignPath Foundation. La firma partirà quando la richiesta a
SignPath Foundation sarà approvata; fino ad allora l'installer non è firmato.

- Chi modifica e rivede il codice: [jackfaz](https://github.com/jackfaz)
- Chi approva le release da firmare: [jackfaz](https://github.com/jackfaz)

Vengono firmati solo gli installer compilati da GitHub Actions a partire da questo repository.

GlucoBar non trasmette nessuna informazione ad altri sistemi in rete, se non su richiesta
esplicita di chi lo installa o lo usa. Le uniche connessioni sono verso i server del
produttore del sensore (Abbott LibreView o Dexcom Share), con l'account inserito dall'utente.

## Perché "sulla" barra e non "dentro"?

Su Windows 11 25H2 una finestra agganciata alla barra (`SetParent` su `Shell_TrayWnd`, la
tecnica di TrafficMonitor) viene disegnata *sotto* lo sfondo acrilico della barra e non si vede.
GlucoBar tiene invece una finestra trasparente, senza bordi e sempre in primo piano esattamente
sopra la barra, e la riporta sopra ogni 500 ms.

## Compilare dai sorgenti

```bat
pip install -r requirements.txt pyinstaller
python -m unittest discover -s tests
python run_glucobar.py --mode desktop          :: avvio senza compilare
pyinstaller --noconfirm --clean glucobar.spec
python tools\previews_to_bmp.py
iscc /DAppVersion=0.5.2 installer\glucobar.iss    :: serve Inno Setup 6
```

Le release le crea GitHub Actions (`.github/workflows/build.yml`): in *Actions → Build installer →
Run workflow* spunta *release* per pubblicare la versione scritta in `glucobar/__init__.py`
(funziona anche pubblicando un tag tipo `v0.5.2`). Le anteprime delle modalità si creano con
`tools/compose_previews.py`.

## Riconoscimenti e marchi

GlucoBar è un progetto open source indipendente, non affiliato né approvato da Abbott o
Dexcom. FreeStyle, Libre, LibreLink e LibreLinkUp sono marchi di Abbott; Dexcom è un marchio
di Dexcom, Inc. I dettagli delle API LibreLinkUp e Dexcom Share vengono dal lavoro della
comunità open source sul diabete (Nightscout, pydexcom e altri).

GlucoBar è gratuito e lo resterà. Se ti è utile e vuoi sostenerlo, puoi
[fare una donazione con PayPal](https://paypal.me/giacomofazioli).

Licenza: [MIT](LICENSE).

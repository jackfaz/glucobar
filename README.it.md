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
  <a href="https://github.com/jackfaz/glucobar/releases/latest"><b>⬇️ Scarica per Windows</b></a> ·
  <a href="#installazione">Installazione</a> ·
  <a href="#uso">Uso</a> ·
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="README.md">🇬🇧 English</a>
</p>

GlucoBar legge l'ultimo valore del sensore da **LibreLinkUp** (il servizio di condivisione di
Abbott) e lo mostra sul PC, colorato, con la freccia di tendenza e da quanti minuti è stato
misurato.

- 🩸 **Sempre sotto gli occhi**: sulla barra accanto all'orologio, in una finestrella, in un
  pannello sul desktop o come icona col numero. Scegli qualsiasi combinazione.
- 📈 **I dettagli quando li vuoi**: grafico fino a 12 ore, media, minimo, massimo, tempo nel
  range, variazione in 15 minuti, giorno del sensore.
- 🖥️ **Secondo monitor** e **schermo intero**: si nasconde durante video e giochi.
- 🔒 **Privato**: password cifrata nel Gestione credenziali di Windows, dati inviati solo ad Abbott.
- 🌍 **6 lingue**: italiano, inglese, spagnolo, francese, tedesco, portoghese.
- 🆓 **Gratuito e open source** (MIT), senza permessi di amministratore.

Scegli cosa mostrare, **anche più cose insieme**, durante l'installazione, e cambialo quando vuoi
col clic destro su qualsiasi elemento di GlucoBar (menu *Mostra*): lì trovi anche unità, lingua,
account ed esci.

| Sulla barra (consigliata) | Finestrella |
|---|---|
| ![Barra](docs/preview_taskbar.png) | ![Finestrella](docs/preview_window.png) |
| Valore, freccia e minuti accanto all'orologio. Funziona anche sul secondo monitor; si nasconde con i video a schermo intero. | Piccola finestra sempre in primo piano con il grafico delle ultime 3 ore. La trascini dove vuoi. |
| **Pannello sullo sfondo** | **Icona vicino all'orologio** |
| ![Pannello sullo sfondo](docs/preview_desktop.png) | ![Icona vicino all'orologio](docs/preview_tray.png) |
| Pannello sul desktop, dietro le finestre: grafico grande (3, 6 o 12 ore), media, minimo, massimo, tempo nel range, variazione in 15 minuti e giorno del sensore. Lo sposti e lo ridimensioni dall'angolo in basso a destra. | Il numero colorato in un'icona vicino all'orologio; passandoci sopra vedi freccia e minuti. Facoltativa: togli la spunta se non la vuoi. |

Verde = nel range (70–180 mg/dL) · Arancione = sopra 180 · Rosso = sotto 70 o sopra 250 ·
Grigio = dato di più di 15 minuti fa.

Lingue: italiano, inglese, spagnolo, francese, tedesco, portoghese.

> ⚠️ **GlucoBar non è un dispositivo medico.** Non usarlo per decidere dosi di insulina o per
> trattare un'ipo: fa fede il lettore o l'app ufficiale. Usa un'**API non ufficiale** che
> Abbott può cambiare in qualsiasi momento.

## Installazione

1. **Attiva LibreLinkUp (una volta sola).** Nell'app **LibreLink** sul telefono: *Condividi →
   App collegate → LibreLinkUp → Aggiungi* e invita un indirizzo email (meglio diverso da
   quello di LibreLink). Installa l'app **LibreLinkUp**, accedi con quell'email, accetta
   l'invito e i termini d'uso. Dopo puoi disinstallare LibreLinkUp.
2. Scarica `GlucoBar-Setup-x.y.z.exe` dalla pagina [Release](../../releases/latest) e avvialo.
   Non servono permessi di amministratore.
3. Scegli la lingua dell'installazione, spunta cosa mostrare (con le anteprime) e se avviare
   GlucoBar all'accensione del PC.
4. Al primo avvio inserisci email e password dell'account **LibreLinkUp**.

Windows può mostrare *"Windows ha protetto il PC"* perché l'installer non è ancora firmato
digitalmente: clicca *Ulteriori informazioni → Esegui comunque*.

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
glucobar login                 cambia account LibreLinkUp
glucobar start | forget        avvia GlucoBar | cancella password e impostazioni
```

Se GlucoBar è aperto, applica le nuove impostazioni entro due secondi.

Installazione silenziosa con le tue scelte (comoda per script e winget):

```text
GlucoBar-Setup-0.5.0.exe /VERYSILENT /ELEMENTS=taskbar,tray /LANG=it
```

## Impostazioni

`%APPDATA%\GlucoBar\config.json`:

| Chiave | Predefinito | Significato |
|---|---|---|
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

- La password è salvata **cifrata nel Gestione credenziali di Windows** (voce
  `GlucoBar:LibreLinkUp`), mai nel file delle impostazioni.
- GlucoBar comunica **solo con i server LibreView di Abbott**. Nessuna statistica, nessun altro server.
- La disinstallazione chiede se eliminare anche impostazioni e password (anche il vecchio
  `.glicemia_widget.json`). Puoi farlo anche in qualsiasi momento con `GlucoBar.exe --forget`.

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
iscc /DAppVersion=0.5.0 installer\glucobar.iss    :: serve Inno Setup 6
```

Le release le crea GitHub Actions (`.github/workflows/build.yml`): pubblica un tag tipo `v0.5.0`
e l'installer viene allegato a una nuova release. Le anteprime delle modalità si creano con
`tools/compose_previews.py`.

## Riconoscimenti e marchi

GlucoBar è un progetto open source indipendente, non affiliato né approvato da Abbott.
FreeStyle, Libre, LibreLink e LibreLinkUp sono marchi di Abbott. I dettagli dell'API
LibreLinkUp vengono dal lavoro della comunità open source sul diabete.

Licenza: [MIT](LICENSE).

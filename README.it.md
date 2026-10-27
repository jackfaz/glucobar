# GlucoBar

**La glicemia del tuo FreeStyle Libre sul desktop di Windows.**

🇬🇧 [Read in English](README.md)

GlucoBar legge l'ultimo valore del sensore da **LibreLinkUp** (il servizio di condivisione di
Abbott) e lo mostra sul PC, colorato, con la freccia di tendenza e da quanti minuti è stato
misurato.

**Un'unica icona di GlucoBar** sta vicino all'orologio: mostra il valore e, col clic destro,
ti fa cambiare modalità, unità e lingua, cambiare account o chiudere. Scegli la modalità durante
l'installazione e cambiala quando vuoi:

| Sulla barra (consigliata) | Finestrella |
|---|---|
| ![Barra](docs/preview_taskbar.png) | ![Finestrella](docs/preview_window.png) |
| Valore, freccia e minuti accanto all'orologio. Funziona anche sul secondo monitor; si nasconde con i video a schermo intero. | Piccola finestra sempre in primo piano con il grafico delle ultime 3 ore. La trascini dove vuoi. |
| **Pannello sullo sfondo** | **Solo icona** |
| ![Pannello sullo sfondo](docs/preview_desktop.png) | ![Solo icona](docs/preview_tray.png) |
| Pannello sul desktop, dietro le finestre: grafico grande (3, 6 o 12 ore), media, minimo, massimo, tempo nel range, variazione in 15 minuti e giorno del sensore. Lo sposti e lo ridimensioni dall'angolo in basso a destra. | Solo il numero colorato nell'icona; passandoci sopra vedi freccia e minuti. |

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
3. Scegli la modalità (con anteprima) e se avviare GlucoBar all'accensione del PC.
4. Al primo avvio inserisci email e password dell'account **LibreLinkUp**.

Windows può mostrare *"Windows ha protetto il PC"* perché l'installer non è ancora firmato
digitalmente: clicca *Ulteriori informazioni → Esegui comunque*.

## Uso

- **Clic destro sull'icona di GlucoBar** vicino all'orologio (o sul valore): aggiorna, modalità,
  unità, lingua, cambia account, esci. **Doppio clic**: aggiorna subito.
- Windows 11 nasconde le icone nuove sotto la freccetta **^**: trascina l'icona di GlucoBar
  sulla barra per tenerla sempre visibile.
- Barra sul secondo monitor: attiva *Impostazioni → Personalizzazione → Barra delle applicazioni →
  Comportamenti della barra delle applicazioni → Mostra la barra delle applicazioni su tutti gli
  schermi*, poi clic destro sul valore → *Sposta sull'altro monitor*.
- Pannello sullo sfondo: trascinalo per spostarlo, trascina l'angolo in basso a destra per
  ridimensionarlo, clic destro per il periodo del grafico e per bloccarlo.

## Impostazioni

`%APPDATA%\GlucoBar\config.json`:

| Chiave | Predefinito | Significato |
|---|---|---|
| `mode` | `taskbar` | `taskbar`, `window`, `desktop` o `tray` (solo icona) |
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
- La disinstallazione chiede se eliminare anche impostazioni e password.

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
iscc /DAppVersion=0.2.0 installer\glucobar.iss    :: serve Inno Setup 6
```

Le release le crea GitHub Actions (`.github/workflows/build.yml`): pubblica un tag tipo `v0.2.0`
e l'installer viene allegato a una nuova release. Le anteprime delle modalità si creano con
`tools/compose_previews.py`.

## Riconoscimenti e marchi

GlucoBar è un progetto open source indipendente, non affiliato né approvato da Abbott.
FreeStyle, Libre, LibreLink e LibreLinkUp sono marchi di Abbott. I dettagli dell'API
LibreLinkUp vengono dal lavoro della comunità open source sul diabete.

Licenza: [MIT](LICENSE).

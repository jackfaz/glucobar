# GlucoBar

**La glicemia del tuo FreeStyle Libre sul desktop di Windows.**

🇬🇧 [Read in English](README.md)

GlucoBar legge l'ultimo valore del sensore da **LibreLinkUp** (il servizio di condivisione di
Abbott) e lo mostra sul PC, colorato, con la freccia di tendenza e da quanti minuti è stato
misurato. Tre modalità, ne scegli una o più durante l'installazione:

| Modalità | Com'è |
|---|---|
| **Barra** (consigliata) | Valore, freccia e minuti sulla barra delle applicazioni, accanto all'orologio. Funziona anche sul secondo monitor. Si nasconde quando un programma è a schermo intero. |
| **Finestra** | Finestrella senza bordi sempre in primo piano, con il grafico delle ultime 3 ore. La trascini dove vuoi. |
| **Icona** | Il numero come icona nell'area di notifica; passandoci sopra vedi freccia e minuti. |

Verde = nel range (70–180 mg/dL) · Arancione = sopra 180 · Rosso = sotto 70 o sopra 250 ·
Grigio = dato di più di 15 minuti fa.

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
3. Scegli le modalità e se avviare GlucoBar all'accensione del PC.
4. Al primo avvio inserisci email e password dell'account **LibreLinkUp**.

Windows può mostrare *"Windows ha protetto il PC"* perché l'installer non è ancora firmato
digitalmente: clicca *Ulteriori informazioni → Esegui comunque*.

## Uso

- **Clic destro** sul valore: aggiorna, mg/dL ↔ mmol/L, sposta a sinistra/destra o sull'altro
  monitor, esci.
- **Doppio clic**: aggiorna subito.
- Secondo monitor: attiva *Impostazioni → Personalizzazione → Barra delle applicazioni →
  Comportamenti della barra delle applicazioni → Mostra la barra delle applicazioni su tutti gli schermi*.
- Windows 11 nasconde le icone nuove sotto la freccetta **^**: trascina l'icona di GlucoBar sulla barra.

## Impostazioni

`%APPDATA%\GlucoBar\config.json`:

| Chiave | Predefinito | Significato |
|---|---|---|
| `low` / `high` / `very_high` | 70 / 180 / 250 | Soglie in mg/dL |
| `unit` | `mg/dL` | oppure `mmol/L` |
| `stale_minutes` | 15 | Oltre questo il valore diventa grigio |
| `refresh_seconds` | 60 | Ogni quanto leggere il dato |
| `language` | `auto` | `it` o `en` |
| `taskbar_monitor` | 1 | 1 = monitor principale, 2 = secondo, … |
| `taskbar_offset` | 0 | Pixel di spostamento (negativo = a sinistra) |
| `taskbar_bg` | auto | Colore della tua barra, es. `#202020`, se vedi un alone attorno alle cifre |
| `taskbar_transparent` | true | `false` per uno sfondo pieno |

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
python run_glucobar.py --mode taskbar        :: avvio senza compilare
pyinstaller --noconfirm --clean glucobar.spec
iscc /DAppVersion=0.1.0 installer\glucobar.iss   :: serve Inno Setup 6
```

Le release le crea GitHub Actions (`.github/workflows/build.yml`): pubblica un tag tipo `v0.1.0`
e l'installer viene allegato a una nuova release.

## Riconoscimenti e marchi

GlucoBar è un progetto open source indipendente, non affiliato né approvato da Abbott.
FreeStyle, Libre, LibreLink e LibreLinkUp sono marchi di Abbott. I dettagli dell'API
LibreLinkUp vengono dal lavoro della comunità open source sul diabete.

Licenza: [MIT](LICENSE).

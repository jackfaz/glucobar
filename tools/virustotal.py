"""Carica un file su VirusTotal e stampa il link alla scansione.

Uso: python tools/virustotal.py [--wait] dist-installer/GlucoBar-Setup-0.11.6.exe
Serve la chiave API gratuita di VirusTotal nella variabile VT_API_KEY (in GitHub
Actions: il secret VT_API_KEY). Senza chiave non fa nulla e non stampa nessun link.
Il link usa l'impronta SHA-256 del file: chiunque può controllare che il file
scaricato dalla release sia lo stesso che è stato scansionato.
Con --wait aspetta la fine dell'analisi e riporta gli antivirus che segnalano il
file (in GitHub Actions anche come avvisi del job, leggibili senza aprire il log, e
nell'output "microsoft" del passo: true se lo segnala Windows Defender).
"""

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

API = "https://www.virustotal.com/api/v3"
DIRECT_LIMIT = 32 * 1024 * 1024  # oltre, VirusTotal vuole un indirizzo di upload apposito


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def report_url(path):
    return f"https://www.virustotal.com/gui/file/{sha256(path)}"


def multipart(path):
    boundary = uuid.uuid4().hex
    with open(path, "rb") as f:
        data = f.read()
    body = (f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; '
            f'filename="{os.path.basename(path)}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n").encode() + data + \
           f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def request(url, key, body=None, content_type=None, tries=4):
    """Una richiesta all'API; riprova se VirusTotal è occupato (429, limite di 4
    richieste al minuto) o ha un problema suo (5xx, rete)."""
    headers = {"x-apikey": key, "accept": "application/json"}
    if content_type:
        headers["content-type"] = content_type
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, body, headers),
                                        timeout=300) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500 or attempt == tries - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == tries - 1:
                raise
        time.sleep(30 * (attempt + 1))


def upload(path, key):
    """Carica il file e restituisce l'id dell'analisi."""
    url = f"{API}/files"
    if os.path.getsize(path) > DIRECT_LIMIT:
        url = request(f"{API}/files/upload_url", key)["data"]
    body, content_type = multipart(path)
    return request(url, key, body, content_type)["data"]["id"]


def wait(analysis_id, key, timeout=900):
    """Aspetta la fine dell'analisi; restituisce (statistiche, {antivirus: nome})."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            attrs = request(f"{API}/analyses/{analysis_id}", key)["data"]["attributes"]
        except urllib.error.HTTPError as e:
            # subito dopo il caricamento l'analisi può non esistere ancora (404)
            if e.code != 404 or time.monotonic() > deadline:
                raise RuntimeError(f"analisi {analysis_id}: {e}") from e
            attrs = {}
        if attrs.get("status") == "completed" or time.monotonic() > deadline:
            break
        time.sleep(30)
    flagged = {engine: r.get("result") or r.get("category")
               for engine, r in attrs.get("results", {}).items()
               if r.get("category") in ("malicious", "suspicious")}
    return attrs.get("stats", {}), flagged


def summary(stats, flagged):
    lines = [f"{stats.get('malicious', 0)} malicious, {stats.get('suspicious', 0)} suspicious, "
             f"{stats.get('undetected', 0)} undetected"]
    lines += [f"{engine}: {name}" for engine, name in sorted(flagged.items())]
    return lines


if __name__ == "__main__":
    args = sys.argv[1:]
    should_wait = "--wait" in args
    path = [a for a in args if a != "--wait"][0]
    key = os.environ.get("VT_API_KEY", "").strip()
    if not key:
        print("VT_API_KEY non impostata: scansione VirusTotal saltata", file=sys.stderr)
        sys.exit(0)
    try:
        try:
            analysis = upload(path, key)
        except Exception as e:
            raise RuntimeError(f"caricamento: {e}") from e
        stats, flagged = wait(analysis, key) if should_wait else (None, None)
    except Exception as e:
        # VirusTotal irraggiungibile: la release esce lo stesso, senza il link alla scansione
        print(f"::warning title=VirusTotal non disponibile::{e!r}", file=sys.stderr)
        sys.exit(0)
    print(report_url(path))
    if should_wait:
        lines = summary(stats, flagged)
        for line in lines:
            print(line, file=sys.stderr)
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::notice title=VirusTotal {os.path.basename(path)}::{' | '.join(lines)}",
                  file=sys.stderr)
        if os.environ.get("GITHUB_OUTPUT"):
            # Windows Defender è l'antivirus di quasi tutti gli utenti: se segnala il file,
            # la release esce come pre-release (vedi .github/workflows/build.yml)
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
                out.write(f"microsoft={'true' if 'Microsoft' in flagged else 'false'}\n")

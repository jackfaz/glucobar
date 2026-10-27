"""Carica un file su VirusTotal e stampa il link alla scansione.

Uso: python tools/virustotal.py dist-installer/GlucoBar-Setup-0.5.2.exe
Serve la chiave API gratuita di VirusTotal nella variabile VT_API_KEY (in GitHub
Actions: il secret VT_API_KEY). Senza chiave non fa nulla e non stampa nessun link.
Il link usa l'impronta SHA-256 del file: chiunque può controllare che il file
scaricato dalla release sia lo stesso che è stato scansionato.
"""

import hashlib
import json
import os
import sys
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


def request(url, key, body=None, content_type=None):
    headers = {"x-apikey": key, "accept": "application/json"}
    if content_type:
        headers["content-type"] = content_type
    with urllib.request.urlopen(urllib.request.Request(url, body, headers),
                                timeout=300) as r:
        return json.load(r)


def upload(path, key):
    url = f"{API}/files"
    if os.path.getsize(path) > DIRECT_LIMIT:
        url = request(f"{API}/files/upload_url", key)["data"]
    body, content_type = multipart(path)
    request(url, key, body, content_type)
    return report_url(path)


if __name__ == "__main__":
    key = os.environ.get("VT_API_KEY", "").strip()
    if not key:
        print("VT_API_KEY non impostata: scansione VirusTotal saltata", file=sys.stderr)
        sys.exit(0)
    print(upload(sys.argv[1], key))

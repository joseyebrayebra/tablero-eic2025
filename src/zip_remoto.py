"""Lectura parcial de un ZIP remoto con peticiones HTTP Range (sin bajarlo completo)."""

from __future__ import annotations

import io
import urllib.request
import zipfile

AGENTE = {"User-Agent": "Mozilla/5.0"}


class ArchivoHTTP(io.RawIOBase):
    def __init__(self, url: str):
        self.url, self.pos = url, 0
        cabeza = urllib.request.Request(url, method="HEAD", headers=AGENTE)
        self.tam = int(urllib.request.urlopen(cabeza, timeout=60).headers["Content-Length"])

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = 0) -> int:
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.tam + offset
        return self.pos

    def readinto(self, b) -> int:
        if self.pos >= self.tam or len(b) == 0:
            return 0
        fin = min(self.pos + len(b), self.tam) - 1
        req = urllib.request.Request(self.url, headers={**AGENTE, "Range": f"bytes={self.pos}-{fin}"})
        datos = urllib.request.urlopen(req, timeout=300).read()
        b[: len(datos)] = datos
        self.pos += len(datos)
        return len(datos)


def abrir_zip(url: str) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BufferedReader(ArchivoHTTP(url), buffer_size=4 << 20))

"""Lógica reutilizável da aplicação."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import minify_html


@dataclass(frozen=True)
class Resultado:
    caminho: Path
    bytes_antes: int
    bytes_depois: int
    alterado: bool

    @property
    def economia(self) -> int:
        return self.bytes_antes - self.bytes_depois


def minificar_arquivo(caminho: Path, *, minificar_css: bool = True,
                      minificar_js: bool = True, simular: bool = False) -> Resultado:
    """Minifica um HTML UTF-8 e substitui o arquivo de forma atômica."""
    caminho = Path(caminho)
    original_bytes = caminho.read_bytes()
    tem_bom = original_bytes.startswith(b"\xef\xbb\xbf")
    original = original_bytes.decode("utf-8-sig" if tem_bom else "utf-8")
    reduzido = minify_html.minify(
        original, minify_css=minificar_css, minify_js=minificar_js,
        remove_bangs=True, remove_processing_instructions=True,
    )
    reduzido_bytes = (b"\xef\xbb\xbf" if tem_bom else b"") + reduzido.encode("utf-8")
    alterado = reduzido_bytes != original_bytes
    if alterado and not simular:
        _substituir_atomicamente(caminho, reduzido_bytes)
    return Resultado(caminho, len(original_bytes), len(reduzido_bytes), alterado)


def minificar_pasta(pasta: Path, *, minificar_css: bool = True,
                    minificar_js: bool = True, simular: bool = False
                    ) -> tuple[list[Resultado], list[tuple[Path, Exception]]]:
    """Encontra arquivos .html/.htm recursivamente e minifica cada um."""
    arquivos = sorted(p for p in Path(pasta).rglob("*")
                      if p.is_file() and p.suffix.lower() in {".html", ".htm"})
    resultados: list[Resultado] = []
    erros: list[tuple[Path, Exception]] = []
    for caminho in arquivos:
        try:
            resultados.append(minificar_arquivo(
                caminho, minificar_css=minificar_css,
                minificar_js=minificar_js, simular=simular,
            ))
        except (OSError, UnicodeError, ValueError) as erro:
            erros.append((caminho, erro))
    return resultados, erros


def _substituir_atomicamente(caminho: Path, conteudo: bytes) -> None:
    modo = caminho.stat().st_mode
    temporario: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=caminho.parent, delete=False) as arquivo:
            temporario = arquivo.name
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.chmod(temporario, modo)
        os.replace(temporario, caminho)
    finally:
        if temporario is not None and os.path.exists(temporario):
            os.unlink(temporario)

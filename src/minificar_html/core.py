"""Lógica reutilizável da aplicação."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import rcssmin
import rjsmin


_NOME_TAG = re.compile(r"<\s*(/?)\s*([a-zA-Z][\w:-]*)")
_TIPO_ATRIBUTO = re.compile(
    r"\btype\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))", re.IGNORECASE
)
_TIPOS_JAVASCRIPT = {
    "application/ecmascript", "application/javascript", "module",
    "text/ecmascript", "text/javascript",
}


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
    reduzido = minificar_conteudo(
        original, minificar_css=minificar_css, minificar_js=minificar_js
    )
    reduzido_bytes = (b"\xef\xbb\xbf" if tem_bom else b"") + reduzido.encode("utf-8")
    alterado = reduzido_bytes != original_bytes
    if alterado and not simular:
        _substituir_atomicamente(caminho, reduzido_bytes)
    return Resultado(caminho, len(original_bytes), len(reduzido_bytes), alterado)


def minificar_conteudo(html: str, *, minificar_css: bool = True,
                       minificar_js: bool = True) -> str:
    """Compacta o HTML sem reescrever tags e trata CSS/JS separadamente."""
    partes: list[str] = []
    posicao = 0
    tamanho = len(html)
    while posicao < tamanho:
        inicio = html.find("<", posicao)
        if inicio < 0:
            partes.append(html[posicao:])
            break
        partes.append(html[posicao:inicio])
        fim = _fim_da_tag(html, inicio)
        if fim is None:
            partes.append(html[inicio:])
            break
        tag = html[inicio:fim]
        partes.append(tag)
        identificacao = _NOME_TAG.match(tag)
        posicao = fim
        if not identificacao or identificacao.group(1):
            continue
        nome = identificacao.group(2).lower()
        if nome not in {"script", "style", "pre", "textarea"} or tag.rstrip().endswith("/>"):
            continue
        fechamento = re.search(rf"</\s*{re.escape(nome)}\s*>", html[posicao:], re.IGNORECASE)
        if not fechamento:
            partes.append(html[posicao:])
            break
        inicio_fechamento = posicao + fechamento.start()
        fim_fechamento = posicao + fechamento.end()
        conteudo = html[posicao:inicio_fechamento]
        if nome == "style" and minificar_css and _tipo_css(tag):
            conteudo = rcssmin.cssmin(conteudo)
        elif nome == "script" and minificar_js and _tipo_javascript(tag):
            conteudo = rjsmin.jsmin(conteudo)
        partes.extend((conteudo, html[inicio_fechamento:fim_fechamento]))
        posicao = fim_fechamento

    return _compactar_espaco_entre_tags(partes)


def _fim_da_tag(html: str, inicio: int) -> int | None:
    if html.startswith("<!--", inicio):
        fim = html.find("-->", inicio + 4)
        return None if fim < 0 else fim + 3
    aspas: str | None = None
    for indice in range(inicio + 1, len(html)):
        caractere = html[indice]
        if aspas:
            if caractere == aspas:
                aspas = None
        elif caractere in {'"', "'"}:
            aspas = caractere
        elif caractere == ">":
            return indice + 1
    return None


def _compactar_espaco_entre_tags(partes: list[str]) -> str:
    resultado: list[str] = []
    for indice, parte in enumerate(partes):
        if (parte and parte.isspace() and indice > 0 and indice + 1 < len(partes)
                and partes[indice - 1].endswith(">") and partes[indice + 1].startswith("<")):
            resultado.append(" ")
        else:
            resultado.append(parte)
    return "".join(resultado)


def _tipo_da_tag(tag: str) -> str | None:
    encontrado = _TIPO_ATRIBUTO.search(tag)
    if not encontrado:
        return None
    return next(valor for valor in encontrado.groups() if valor is not None).strip().lower()


def _tipo_javascript(tag: str) -> bool:
    tipo = _tipo_da_tag(tag)
    return tipo is None or tipo in _TIPOS_JAVASCRIPT


def _tipo_css(tag: str) -> bool:
    tipo = _tipo_da_tag(tag)
    return tipo is None or tipo == "text/css"


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

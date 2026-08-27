from pathlib import Path

from minificar_html.cli import main
from minificar_html.core import minificar_arquivo, minificar_pasta


def test_minifica_html_e_embutidos(tmp_path: Path) -> None:
    arquivo = tmp_path / "index.html"
    arquivo.write_text("""<!doctype html>\n<!-- remover -->
    <style>body { color: red; }</style><h1> Olá mundo </h1>
    <script>const soma = 1 + 2;</script>""", encoding="utf-8")
    resultado = minificar_arquivo(arquivo)
    conteudo = arquivo.read_text(encoding="utf-8")
    assert resultado.alterado and resultado.economia > 0
    assert "<!-- remover -->" not in conteudo


def test_recursivo_ignora_outros_arquivos(tmp_path: Path) -> None:
    sub = tmp_path / "paginas"
    sub.mkdir()
    (tmp_path / "index.HTML").write_text("<p> início </p>", encoding="utf-8")
    (sub / "sobre.htm").write_text("<!-- x --><p>sobre</p>", encoding="utf-8")
    (sub / "dados.txt").write_text("  não alterar  ", encoding="utf-8")
    resultados, erros = minificar_pasta(tmp_path)
    assert len(resultados) == 2 and not erros
    assert (sub / "dados.txt").read_text() == "  não alterar  "


def test_simulacao_e_bom(tmp_path: Path) -> None:
    arquivo = tmp_path / "index.html"
    original = b"\xef\xbb\xbf<!-- x --><p> texto </p>"
    arquivo.write_bytes(original)
    resultado = minificar_arquivo(arquivo, simular=True)
    assert resultado.alterado and arquivo.read_bytes() == original


def test_cli_processa_pasta(tmp_path: Path, capsys) -> None:
    (tmp_path / "index.html").write_text("<!-- x --><p> texto </p>", encoding="utf-8")
    assert main(["--pasta", str(tmp_path)]) == 0
    assert "1 arquivo(s)" in capsys.readouterr().out


def test_cli_rejeita_pasta_ausente(tmp_path: Path, capsys) -> None:
    assert main(["--pasta", str(tmp_path / "ausente")]) == 2
    assert "não existe" in capsys.readouterr().out

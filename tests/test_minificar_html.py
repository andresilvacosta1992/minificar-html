from pathlib import Path

from minificar_html.cli import main
from minificar_html.core import minificar_arquivo, minificar_conteudo, minificar_pasta


def test_minifica_html_e_embutidos(tmp_path: Path) -> None:
    arquivo = tmp_path / "index.html"
    arquivo.write_text("""<!doctype html>\n<!-- remover -->
    <style>body { color: red; }</style><h1> Olá mundo </h1>
    <script>const soma = 1 + 2;</script>""", encoding="utf-8")
    resultado = minificar_arquivo(arquivo)
    conteudo = arquivo.read_text(encoding="utf-8")
    assert resultado.alterado and resultado.economia > 0
    assert "<!-- remover -->" in conteudo
    assert "body{color:red}" in conteudo
    assert "const soma=1+2;" in conteudo


def test_preserva_texto_comentarios_e_valores_de_atributos() -> None:
    original = '''<!-- manter -->\n<DIV data-texto="> <">\n<span>Olá mundo</span>\n</DIV>'''
    reduzido = minificar_conteudo(original)
    assert "<!-- manter -->" in reduzido
    assert '<DIV data-texto="> <">' in reduzido
    assert "<span>Olá mundo</span>" in reduzido
    assert "\n" not in reduzido


def test_compacta_tag_multilinha_e_style_inline() -> None:
    original = '''<img src="foto.png"
        alt="Foto com espaços"
        style=" color: red; margin: 0 10px; "
        data-sinal="> <">'''
    reduzido = minificar_conteudo(original)
    assert "\n" not in reduzido
    assert 'alt="Foto com espaços"' in reduzido
    assert 'style="color:red;margin:0 10px"' in reduzido
    assert 'data-sinal="> <"' in reduzido


def test_preserva_blocos_sensiveis_e_scripts_nao_javascript() -> None:
    original = '''<pre>  linha 1\n  linha 2</pre>
    <textarea>  texto\n  intacto</textarea>
    <script type="application/json"> { "nome": "A B" } </script>
    <script type="importmap"> { "imports": {} } </script>'''
    reduzido = minificar_conteudo(original)
    assert "  linha 1\n  linha 2" in reduzido
    assert "  texto\n  intacto" in reduzido
    assert '{ "nome": "A B" }' in reduzido
    assert '{ "imports": {} }' in reduzido


def test_compacta_json_ld_valido() -> None:
    original = '<script type="application/ld+json"> { "nome": "A B" } </script>'
    assert minificar_conteudo(original) == '<script type="application/ld+json">{"nome":"A B"}</script>'


def test_preserva_json_ld_invalido() -> None:
    original = '<script type="application/ld+json">{{ json_dinamico }}</script>'
    assert minificar_conteudo(original) == original


def test_minifica_css_e_javascript_com_motores_separados() -> None:
    original = '''<style> /* x */ body { color: red; margin: 0 10px; } </style>
    <script> // x\n const mensagem = "olá mundo"; </script>'''
    reduzido = minificar_conteudo(original)
    assert "body{color:red;margin:0 10px}" in reduzido
    assert 'const mensagem="olá mundo";' in reduzido
    assert "/* x */" not in reduzido
    assert "// x" not in reduzido


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
    original = b"\xef\xbb\xbf<!-- x -->\n    <p> texto </p>"
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

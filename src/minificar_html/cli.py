"""Interface de linha de comando."""

import argparse
from pathlib import Path

from .core import minificar_pasta


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="minificar-html",
        description="Minifica recursivamente os arquivos HTML de uma pasta.",
    )
    parser.add_argument("--pasta", required=True, type=Path,
                        help="pasta que contém os arquivos .html e .htm")
    parser.add_argument("--simular", action="store_true",
                        help="mostra o resultado sem alterar os arquivos")
    parser.add_argument("--sem-css", action="store_true", help="não minifica CSS embutido")
    parser.add_argument("--sem-js", action="store_true", help="não minifica JavaScript embutido")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = criar_parser().parse_args(argv)
    pasta: Path = args.pasta.expanduser()
    if not pasta.exists():
        print(f"Erro: a pasta não existe: {pasta}")
        return 2
    if not pasta.is_dir():
        print(f"Erro: o caminho não é uma pasta: {pasta}")
        return 2
    resultados, erros = minificar_pasta(
        pasta, minificar_css=not args.sem_css,
        minificar_js=not args.sem_js, simular=args.simular,
    )
    for resultado in resultados:
        if resultado.alterado:
            acao = "Minificaria" if args.simular else "Minificado"
            print(f"{acao}: {resultado.caminho} (-{resultado.economia} bytes)")
    for caminho, erro in erros:
        print(f"Erro em {caminho}: {erro}")
    alterados = sum(r.alterado for r in resultados)
    economia = sum(r.economia for r in resultados if r.alterado)
    prefixo = "Simulação: " if args.simular else ""
    print(f"{prefixo}{len(resultados) + len(erros)} arquivo(s), "
          f"{alterados} alterado(s), {economia} bytes economizados, "
          f"{len(erros)} erro(s).")
    return 1 if erros else 0


if __name__ == "__main__":
    raise SystemExit(main())

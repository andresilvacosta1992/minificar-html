# minificar-html

Minifica recursivamente todos os arquivos HTML de uma pasta diretamente no local original. Compacta texto e atributos, preserva comentários e conteúdo sensível, e usa ferramentas específicas para CSS, JavaScript e JSON-LD.

## Instalação e uso

```bash
pip install minificar-html
minificar-html --pasta ./meu-site
```

Arquivos `.html` e `.htm` são encontrados recursivamente. Opções adicionais:

```bash
minificar-html --pasta ./meu-site --simular
minificar-html --pasta ./meu-site --sem-css --sem-js
```

`--simular` calcula a economia sem escrever. Blocos `<pre>` e `<textarea>`, import maps e comentários são preservados. Atributos `style` e JSON-LD são minificados pelos processadores de suas respectivas linguagens. Se um arquivo não estiver em UTF-8 ou não puder ser lido, os demais continuam sendo processados e o comando termina com código de erro.

## Desenvolvimento e publicação

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

No upload, use `__token__` como usuário e seu token completo do PyPI como senha.

Licença MIT.

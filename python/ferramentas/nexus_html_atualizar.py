#!/usr/bin/env python3

import sys
import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
GERADOS_DIR = BASE_DIR / "html" / "html_gerados"
INDEX_FILE = GERADOS_DIR / "index.json"


def erro(mensagem, **extra):
    resultado = {
        "ok": False,
        "erro": mensagem
    }
    resultado.update(extra)
    print(json.dumps(resultado, ensure_ascii=False))
    sys.exit(1)


def sucesso(**dados):
    resultado = {
        "ok": True
    }
    resultado.update(dados)
    print(json.dumps(resultado, ensure_ascii=False))
    sys.exit(0)


def escapar_html(texto):
    return (
        texto.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def main():
    if len(sys.argv) < 6:
        erro(
            "Argumentos insuficientes.",
            uso="nexus_html_atualizar.py arquivo titulo preco descricao imagem"
        )

    arquivo = Path(sys.argv[1]).name
    titulo = sys.argv[2]
    preco = sys.argv[3]
    descricao = sys.argv[4]
    imagem = sys.argv[5]

    if not arquivo.endswith(".html"):
        erro("Arquivo HTML inválido.")

    html_file = GERADOS_DIR / arquivo

    if not html_file.exists():
        erro("Arquivo HTML não encontrado.", arquivo=arquivo)

    if not INDEX_FILE.exists():
        erro("index.json não encontrado.")

    try:
        html = html_file.read_text(encoding="utf-8")
    except Exception as exc:
        erro("Não foi possível ler o HTML.", detalhe=str(exc))

    titulo_html = escapar_html(titulo)
    preco_html = escapar_html(preco)
    descricao_html = escapar_html(descricao)

    # ---------------------------------------------------------
    # Atualiza <title>
    # ---------------------------------------------------------
    html, qtd_title = re.subn(
        r"<title>.*?</title>",
        f"<title>{titulo_html}</title>",
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL
    )

    # ---------------------------------------------------------
    # Atualiza o primeiro <h1>
    # ---------------------------------------------------------
    html, qtd_h1 = re.subn(
        r"<h1>.*?</h1>",
        f"<h1>{titulo_html}</h1>",
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL
    )

    # ---------------------------------------------------------
    # Atualiza preço.
    # Suporta classes comuns usadas pelo Studio.
    # ---------------------------------------------------------
    html, qtd_preco = re.subn(
        r'(<(?:div|span|p)[^>]*class=["\'][^"\']*preco[^"\']*["\'][^>]*>).*?(</(?:div|span|p)>)',
        rf"\1{preco_html}\2",
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL
    )

    if qtd_preco == 0:
        html, qtd_preco = re.subn(
            r'(<(?:div|span|p)[^>]*id=["\'][^"\']*(?:produto)?(?:preco|preço)[^"\']*["\'][^>]*>).*?(</(?:div|span|p)>)',
            rf"\1{preco_html}\2",
            html,
            count=1,
            flags=re.IGNORECASE | re.DOTALL
        )

    # ---------------------------------------------------------
    # Atualiza descrição.
    # ---------------------------------------------------------
    html, qtd_descricao = re.subn(
        r'(<(?:div|p|section)[^>]*class=["\'][^"\']*descricao[^"\']*["\'][^>]*>).*?(</(?:div|p|section)>)',
        rf"\1{descricao_html}\2",
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL
    )

    if qtd_descricao == 0:
        html, qtd_descricao = re.subn(
            r'(<(?:div|p|section)[^>]*id=["\'][^"\']*(?:produto)?descricao[^"\']*["\'][^>]*>).*?(</(?:div|p|section)>)',
            rf"\1{descricao_html}\2",
            html,
            count=1,
            flags=re.IGNORECASE | re.DOTALL
        )

    # ---------------------------------------------------------
    # Atualiza imagem.
    #
    # A nova imagem pode ser:
    # data:image/...;base64,...
    #
    # ou uma URL/caminho caso seja uma página antiga.
    # ---------------------------------------------------------
    if imagem:
        imagem_segura = imagem.replace("&", "&amp;").replace('"', "&quot;")

        html, qtd_imagem = re.subn(
            r'(<img\b[^>]*\bsrc=["\']).*?(["\'])',
            rf"\1{imagem_segura}\2",
            html,
            count=1,
            flags=re.IGNORECASE | re.DOTALL
        )
    else:
        qtd_imagem = 0

    # ---------------------------------------------------------
    # Salva HTML
    # ---------------------------------------------------------
    try:
        html_file.write_text(html, encoding="utf-8")
    except Exception as exc:
        erro("Não foi possível salvar o HTML.", detalhe=str(exc))

    # ---------------------------------------------------------
    # Atualiza index.json sem destruir as demais páginas.
    # ---------------------------------------------------------
    try:
        dados = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        erro("index.json inválido.", detalhe=str(exc))

    paginas = dados.get("paginas", [])

    encontrada = False

    for pagina in paginas:
        if pagina.get("arquivo") == arquivo:
            pagina["titulo"] = titulo
            pagina["preco"] = preco
            pagina["descricao"] = descricao

            if imagem:
                pagina["imagem"] = imagem

            encontrada = True
            break

    if not encontrada:
        erro(
            "Página não encontrada no index.json.",
            arquivo=arquivo
        )

    try:
        INDEX_FILE.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception as exc:
        erro("Não foi possível atualizar index.json.", detalhe=str(exc))

    sucesso(
        acao="atualizar_html",
        arquivo=arquivo,
        titulo=titulo,
        preco=preco,
        imagem_atualizada=bool(imagem),
        html_atualizado=True,
        index_atualizado=True
    )


if __name__ == "__main__":
    main()

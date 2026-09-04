#!/usr/bin/env python3

import sys
import json
from pathlib import Path


# ============================================================
# NEXUS HTML STUDIO
# FERRAMENTA DE EXCLUSÃO DE HTML
# ============================================================

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


def nome_seguro(nome):
    """
    Impede caminhos externos.
    Aceita somente o nome do arquivo.
    """
    return Path(str(nome)).name


def main():

    if len(sys.argv) < 2:
        erro("Informe o arquivo HTML que será excluído.")

    arquivo = nome_seguro(sys.argv[1])

    if not arquivo:
        erro("Nome do arquivo inválido.")

    if not arquivo.lower().endswith(".html"):
        erro(
            "Somente arquivos .html podem ser excluídos.",
            arquivo=arquivo
        )

    GERADOS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    html_file = GERADOS_DIR / arquivo

    # --------------------------------------------------------
    # VERIFICA SE O HTML EXISTE
    # --------------------------------------------------------

    if not html_file.exists():
        erro(
            "Arquivo HTML não encontrado.",
            arquivo=arquivo
        )

    # --------------------------------------------------------
    # EXCLUI O HTML
    # --------------------------------------------------------

    try:
        html_file.unlink()
    except Exception as exc:
        erro(
            "Não foi possível excluir o arquivo HTML.",
            arquivo=arquivo,
            detalhe=str(exc)
        )

    # --------------------------------------------------------
    # ATUALIZA INDEX.JSON
    # --------------------------------------------------------

    paginas_removidas = 0

    if INDEX_FILE.exists():

        try:
            dados_index = json.loads(
                INDEX_FILE.read_text(
                    encoding="utf-8"
                )
            )

        except Exception as exc:
            erro(
                "O index.json está inválido.",
                detalhe=str(exc)
            )

        if not isinstance(dados_index, dict):
            erro("O index.json precisa conter um objeto JSON.")

        paginas = dados_index.get("paginas", [])

        if not isinstance(paginas, list):
            erro("O campo paginas do index.json precisa ser uma lista.")

        paginas_novas = []

        for pagina in paginas:

            if isinstance(pagina, dict) and pagina.get("arquivo") == arquivo:
                paginas_removidas += 1
                continue

            paginas_novas.append(pagina)

        dados_index["paginas"] = paginas_novas

        try:
            INDEX_FILE.write_text(
                json.dumps(
                    dados_index,
                    ensure_ascii=False,
                    indent=2
                ),
                encoding="utf-8"
            )

        except Exception as exc:
            erro(
                "O HTML foi excluído, mas não foi possível atualizar o index.json.",
                arquivo=arquivo,
                detalhe=str(exc)
            )

    # --------------------------------------------------------
    # SUCESSO
    # --------------------------------------------------------

    sucesso(
        acao="excluir_html",
        arquivo=arquivo,
        html_excluido=True,
        index_atualizado=INDEX_FILE.exists(),
        paginas_removidas=paginas_removidas
    )


if __name__ == "__main__":
    main()

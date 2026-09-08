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
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def ler_entrada():
    try:
        entrada = sys.stdin.read()
    except Exception as exc:
        erro(
            "Não foi possível ler os dados enviados pelo servidor.",
            detalhe=str(exc)
        )

    if not entrada.strip():
        erro("Nenhum dado foi recebido pelo Python.")

    try:
        dados = json.loads(entrada)
    except Exception as exc:
        erro(
            "Os dados recebidos não são JSON válido.",
            detalhe=str(exc)
        )

    if not isinstance(dados, dict):
        erro("Os dados recebidos precisam ser um objeto JSON.")

    return dados


def main():

    dados = ler_entrada()

    arquivo = Path(str(dados.get("arquivo", ""))).name
    titulo = str(dados.get("titulo", ""))
    preco = str(dados.get("preco", ""))
    descricao = str(dados.get("descricao", ""))
    imagem = str(dados.get("imagem", ""))
    video_url = str(dados.get("video_url", "")).strip()

    if video_url and not re.match(
        r"^https://res\.cloudinary\.com/",
        video_url,
        re.IGNORECASE
    ):
        erro("A URL do vídeo precisa ser uma URL HTTPS válida do Cloudinary.")

    if not arquivo:
        erro("Arquivo HTML não informado.")

    if not arquivo.endswith(".html"):
        erro("Arquivo HTML inválido.", arquivo=arquivo)

    html_file = GERADOS_DIR / arquivo

    if not html_file.exists():
        erro(
            "Arquivo HTML não encontrado.",
            arquivo=arquivo
        )

    if not INDEX_FILE.exists():
        erro("index.json não encontrado.")

    try:
        html = html_file.read_text(encoding="utf-8")
    except Exception as exc:
        erro(
            "Não foi possível ler o HTML.",
            detalhe=str(exc)
        )

    titulo_html = escapar_html(titulo)
    preco_html = escapar_html(preco)
    descricao_html = escapar_html(descricao)

    # TITLE
    html, qtd_title = re.subn(
        r"<title>.*?</title>",
        f"<title>{titulo_html}</title>",
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL
    )

    # H1
    html, qtd_h1 = re.subn(
        r"<h1>.*?</h1>",
        f"<h1>{titulo_html}</h1>",
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL
    )

    # PREÇO POR CLASS
    html, qtd_preco = re.subn(
        r'(<(?:div|span|p)[^>]*class=["\'][^"\']*preco[^"\']*["\'][^>]*>).*?(</(?:div|span|p)>)',
        rf"\1{preco_html}\2",
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL
    )

    # PREÇO POR ID
    if qtd_preco == 0:
        html, qtd_preco = re.subn(
            r'(<(?:div|span|p)[^>]*id=["\'][^"\']*(?:produto)?(?:preco|preço)[^"\']*["\'][^>]*>).*?(</(?:div|span|p)>)',
            rf"\1{preco_html}\2",
            html,
            count=1,
            flags=re.IGNORECASE | re.DOTALL
        )

    # DESCRIÇÃO POR CLASS
    html, qtd_descricao = re.subn(
        r'(<(?:div|p|section)[^>]*class=["\'][^"\']*descricao[^"\']*["\'][^>]*>).*?(</(?:div|p|section)>)',
        rf"\1{descricao_html}\2",
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL
    )

    # DESCRIÇÃO POR ID
    if qtd_descricao == 0:
        html, qtd_descricao = re.subn(
            r'(<(?:div|p|section)[^>]*id=["\'][^"\']*descricao[^"\']*["\'][^>]*>).*?(</(?:div|p|section)>)',
            rf"\1{descricao_html}\2",
            html,
            count=1,
            flags=re.IGNORECASE | re.DOTALL
        )

    # IMAGEM BASE64
    if imagem:

        if not imagem.startswith("data:image/"):
            erro(
                "A imagem precisa estar no formato Base64 data:image/..."
            )

        imagem_segura = (
            imagem
            .replace("&", "&amp;")
            .replace('"', "&quot;")
        )

        html, qtd_imagem = re.subn(
            r'(<img\b[^>]*\bsrc=["\']).*?(["\'])',
            rf"\1{imagem_segura}\2",
            html,
            count=1,
            flags=re.IGNORECASE | re.DOTALL
        )

    else:
        qtd_imagem = 0

    # VÍDEO CLOUDINARY
    # O marcador permite atualizar/remover o vídeo criado pelo Studio
    # sem duplicar o bloco a cada edição.
    marcador_inicio = "<!-- NEXUS_VIDEO_PRODUTO -->"
    marcador_fim = "<!-- FIM_NEXUS_VIDEO_PRODUTO -->"

    padrao_bloco_video = re.compile(
        re.escape(marcador_inicio) +
        r"[\\s\\S]*?" +
        re.escape(marcador_fim),
        re.IGNORECASE
    )

    if video_url:
        video_seguro = escapar_html(video_url)

        bloco_video = f"""<!-- NEXUS_VIDEO_PRODUTO -->
<section class="nexus-video-produto" style="width:100%;margin:24px 0;">
    <div style="width:100%;max-width:900px;margin:0 auto;">
        <video
            controls
            playsinline
            preload="metadata"
            style="display:block;width:100%;height:auto;border-radius:16px;"
            src="{video_seguro}"
        ></video>
    </div>
</section>
<!-- FIM_NEXUS_VIDEO_PRODUTO -->"""

        if padrao_bloco_video.search(html):
            html = padrao_bloco_video.sub(bloco_video, html, count=1)
        else:
            fechamento_body = re.search(
                r"</body>",
                html,
                flags=re.IGNORECASE
            )

            if fechamento_body:
                html = (
                    html[:fechamento_body.start()]
                    + "\n"
                    + bloco_video
                    + "\n"
                    + html[fechamento_body.start():]
                )
            else:
                html += "\n" + bloco_video + "\n"

    else:
        # Se o usuário limpou o campo de vídeo, remove
        # somente o bloco criado pelo NEXUS HTML STUDIO.
        html = padrao_bloco_video.sub("", html, count=1)

    # SALVA HTML
    try:
        html_file.write_text(
            html,
            encoding="utf-8"
        )
    except Exception as exc:
        erro(
            "Não foi possível salvar o HTML.",
            detalhe=str(exc)
        )

    # LÊ INDEX
    try:
        dados_index = json.loads(
            INDEX_FILE.read_text(encoding="utf-8")
        )
    except Exception as exc:
        erro(
            "index.json inválido.",
            detalhe=str(exc)
        )

    paginas = dados_index.get("paginas", [])

    encontrada = False

    for pagina in paginas:

        if pagina.get("arquivo") == arquivo:

            pagina["titulo"] = titulo
            pagina["preco"] = preco
            pagina["descricao"] = descricao

            if imagem:
                pagina["imagem"] = imagem

            pagina["video_url"] = video_url

            encontrada = True
            break

    if not encontrada:
        erro(
            "Página não encontrada no index.json.",
            arquivo=arquivo
        )

    # SALVA INDEX
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
            "Não foi possível atualizar index.json.",
            detalhe=str(exc)
        )

    sucesso(
        acao="atualizar_html",
        arquivo=arquivo,
        titulo=titulo,
        preco=preco,
        imagem_atualizada=bool(imagem),
        tamanho_imagem_base64=len(imagem),
        html_atualizado=True,
        index_atualizado=True
    )


if __name__ == "__main__":
    main()

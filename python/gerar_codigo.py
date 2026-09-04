#!/usr/bin/env python3

import os
from pathlib import Path
from dotenv import load_dotenv
import sys
import json
import urllib.request
import urllib.error
import time
import subprocess
from datetime import datetime

print("=== NEXUS GERADOR DE CÓDIGO ===")

if len(sys.argv) < 2:
    print("Erro: nenhuma solicitação recebida.")
    raise SystemExit(1)

solicitacao = " ".join(sys.argv[1:]).strip()
print(f"Solicitação: {solicitacao}\n")

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("ERRO: GEMINI_API_KEY não encontrada.")
    raise SystemExit(1)

prompt = """
Você é o gerador do NEXUS HTML STUDIO.
Usuário solicitou: __SOLICITACAO__
Gere HTML completo, moderno, responsivo.

DESCRIÇÃO:
mínimo 500 chars, persuasiva, final incluir
"✨ Dúvidas? Fale com nossa assistente virtual e depois com a vendedora Kellen: (55) 98101-1208"

BOTOES:

1. "💬 Comprar pelo WhatsApp"
#25D366
https://wa.me/5555981011208?text=Olá%20Kellen%21%20Quero%20[NOME]

2. "📤 Compartilhar página"
#2a3441
navigator.share fallback copiar

3. "🤖 Falar com Atendimento Meta AI"
#6c2bd9

ABRE WHATSAPP AUTOMATICO COM TEXTO:

const nome = document.querySelector('h1')?.innerText || 'Produto';
const preco = document.querySelector('.preco, [class*=price]')?.innerText || 'Consulte';
const desc = document.querySelector('.descricao, [class*=desc]')?.innerText || '';

const promptMetaAI = `PROMPT PADRÃO — ATENDENTE VIRTUAL DE VENDAS

Atue exclusivamente como atendente virtual deste anúncio.

Sua função é atender o cliente, tirar dúvidas sobre o produto apresentado neste anúncio e ajudá-lo a tomar a decisão de compra.

Use as informações do anúncio como referência principal. Seja educado, objetivo, cordial e persuasivo, sem inventar informações que não estejam disponíveis no anúncio.

Quando o cliente demonstrar interesse, conduza a conversa naturalmente para a compra e incentive-o a entrar em contato pelo canal de compra informado no anúncio.

Não saia do contexto do produto. Se o cliente perguntar sobre assuntos que não tenham relação com este produto ou com a compra, informe educadamente que você está disponível para ajudar somente com informações e atendimento relacionados ao produto anunciado.

Nunca invente preço, desconto, estoque, características, prazo de entrega, garantia ou condições de pagamento que não estejam informados no anúncio.

OBJETIVO PRINCIPAL:
Atender o cliente e ajudá-lo a comprar o produto anunciado.`;

const texto = `${promptMetaAI}

INFORMAÇÕES DO PRODUTO:
Nome: ${nome}
Preço: ${preco}
Descrição: ${desc.substring(0,600)}
Link: ${location.href}

Kellen (55) 98101-1208
Me mostre as vantagens deste produto e me ajude a comprar?`;

const urlMeta = `https://wa.me/ais/867051314767696?s=5&text=${encodeURIComponent(texto)}`;

window.open(urlMeta, '_blank');

BOTAO CSS:
display:block;
width:100%;
box-sizing:border-box;
margin-top:12px;
padding:15px;
border-radius:12px;
text-align:center;
font-weight:bold;
font-size:16px;
border:none;
cursor:pointer;

ZOOM:
duplo toque scale(2)

SAIDA:
SOMENTE HTML
""".replace("__SOLICITACAO__", solicitacao)

url = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.1-flash-lite:generateContent?key=" + api_key
)

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": prompt
                }
            ]
        }
    ],
    "generationConfig": {
        "temperature": 0.5,
        "maxOutputTokens": 8192
    }
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json"
    },
    method="POST"
)

resultado = None

for tentativa in range(1, 4):

    try:

        print(f"Tentativa Gemini {tentativa}/3...")

        with urllib.request.urlopen(req, timeout=90) as r:
            resultado = json.loads(
                r.read().decode("utf-8")
            )

        break

    except urllib.error.HTTPError as e:

        if e.code == 503 and tentativa < 3:
            time.sleep(tentativa * 5)
            continue

        print(
            e.read().decode(
                "utf-8",
                errors="replace"
            )
        )

        raise SystemExit(1)

    except Exception as e:

        if tentativa < 3:
            time.sleep(tentativa * 3)
            continue

        print(f"Erro Gemini: {e}")
        raise SystemExit(1)

if not resultado:
    print("ERRO: Gemini não retornou resultado.")
    raise SystemExit(1)

try:

    codigo_html = (
        resultado["candidates"][0]
        ["content"]["parts"][0]["text"]
        .strip()
    )

except (KeyError, IndexError, TypeError):

    print("ERRO: resposta inesperada do Gemini.")
    print(json.dumps(
        resultado,
        ensure_ascii=False,
        indent=2
    ))

    raise SystemExit(1)

if codigo_html.startswith("```"):

    linhas = codigo_html.splitlines()

    if linhas and linhas[0].startswith("```"):
        linhas = linhas[1:]

    if linhas and linhas[-1].strip() == "```":
        linhas = linhas[:-1]

    codigo_html = "\n".join(linhas).strip()

print("=== CÓDIGO GERADO ===\n")
print(codigo_html)
print()

PASTA_HTML = (
    Path(__file__).resolve().parent.parent
    / "html"
    / "html_gerados"
)

PASTA_HTML.mkdir(
    parents=True,
    exist_ok=True
)

arquivo_html = (
    PASTA_HTML
    / (
        "nexus_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".html"
    )
)

# ============================================================
# SALVAR HTML LOCALMENTE PRIMEIRO
# ============================================================

try:

    arquivo_html.write_text(
        codigo_html,
        encoding="utf-8"
    )

except Exception as erro:

    print(
        f"ERRO: não foi possível salvar o HTML: {erro}"
    )

    raise SystemExit(1)

print()
print("=== HTML SALVO ===")
print(str(arquivo_html))

# ============================================================
# SINCRONIZAÇÃO FIREBASE
#
# IMPORTANTE:
# A sincronização acontece SOMENTE depois que o HTML
# foi salvo com sucesso.
#
# Se o Firebase estiver indisponível ou sem credencial,
# a geração do HTML NÃO será desfeita.
# ============================================================

SINCRONIZADOR = (
    Path(__file__).resolve().parent
    / "ferramentas"
    / "nexus_firebase_sync.py"
)

if SINCRONIZADOR.exists():

    print()
    print("=== SINCRONIZAÇÃO FIREBASE ===")

    try:

        resultado_sync = subprocess.run(
            [
                sys.executable,
                str(SINCRONIZADOR),
                "salvar",
                arquivo_html.name
            ],
            cwd=str(BASE_DIR),
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=60
        )

        if resultado_sync.stdout:
            print(resultado_sync.stdout)

        if resultado_sync.stderr:
            print(
                resultado_sync.stderr,
                file=sys.stderr
            )

        if resultado_sync.returncode == 0:

            print(
                "✅ Cópia do HTML sincronizada com Firebase."
            )

        else:

            print(
                "⚠️ Firebase não sincronizado."
            )

            print(
                "O HTML local continua salvo normalmente."
            )

    except subprocess.TimeoutExpired:

        print(
            "⚠️ Tempo limite da sincronização Firebase."
        )

        print(
            "O HTML continua salvo no Render."
        )

    except Exception as erro:

        print(
            f"⚠️ Erro na sincronização Firebase: {erro}"
        )

        print(
            "O HTML continua salvo normalmente."
        )

else:

    print(
        "⚠️ Sincronizador Firebase não encontrado."
    )

    print(
        f"Esperado em: {SINCRONIZADOR}"
    )

print()
print("=== FIM DO HTML SALVO ===")
print()
print("=== FIM DO CÓDIGO ===")

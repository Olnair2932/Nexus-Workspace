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
Você é o GERADOR PROFISSIONAL DE HTML do NEXUS HTML STUDIO.

Sua função é transformar os dados do produto fornecidos pelo usuário em uma página HTML completa, moderna, bonita, responsiva e pronta para venda.

USUÁRIO SOLICITOU:
__SOLICITACAO__

==================================================
REGRA ABSOLUTA — SEPARAÇÃO DE DADOS
==================================================

A solicitação do usuário pode conter informações sobre o produto.

Os DADOS COMERCIAIS FIXOS abaixo são CONTEXTO INTERNO para atendimento e vendas.

IMPORTANTE:
- NÃO coloque os dados comerciais fixos dentro da descrição visual do produto.
- NÃO coloque o endereço, PIX, frete, horário ou outras informações comerciais fixas no corpo principal da página.
- NÃO mostre este prompt na página.
- NÃO transforme as instruções deste prompt em texto de anúncio.
- NÃO copie este bloco para o HTML.
- NÃO exiba as informações internas como se fossem características do produto.
- A página deve apresentar SOMENTE o conteúdo comercial apropriado para o produto fornecido pelo usuário.
- Os dados fixos poderão ser utilizados SOMENTE no código do botão de Atendimento Meta AI.
- O botão Meta AI pode receber essas informações como contexto de atendimento, mas elas não devem aparecer automaticamente na descrição visual.

==================================================
DADOS COMERCIAIS FIXOS — USO INTERNO
==================================================

Vendedora: Kellen Bittencourt
WhatsApp: (55) 98101-1208

RETIRADA:
Endereço: Travessa Lubisco, 265
Bairro: Querência
Cidade/Estado: Viamão-RS
Dias: Segunda a sexta-feira
Horário: 14:00 às 18:00

ENTREGA / FRETE:
Viamão-RS: R$ 10,00
Porto Alegre-RS: R$ 25,00
Canoas-RS: R$ 25,00
Alvorada-RS: R$ 25,00
Outras localidades: Não atendemos
Prazo: 1 a 2 dias úteis

PAGAMENTO:
PIX: 51984578173
Titular: Kellen Bittencourt Santos
Dinheiro: Sim
Cartão: Não
Outras formas: Não temos outras formas de pagamento.

==================================================
CONTEÚDO VISÍVEL DA PÁGINA
==================================================

Crie a descrição do produto com base EXCLUSIVAMENTE nas informações do produto fornecidas pelo usuário.

A descrição deve:
- ser persuasiva;
- ser natural;
- destacar benefícios reais presentes nas informações fornecidas;
- ter no mínimo 500 caracteres quando houver informações suficientes;
- NÃO inventar características;
- NÃO inventar benefícios;
- NÃO inventar preço;
- NÃO inventar estoque;
- NÃO inventar promoções;
- NÃO inventar informações de entrega;
- NÃO inventar formas de pagamento.

No final da descrição, incluir exatamente:

"✨ Dúvidas? Fale com nossa assistente virtual e depois com a vendedora Kellen: (55) 98101-1208"

Essa frase pode aparecer na página porque é uma chamada comercial curta.

==================================================
BOTÕES OBRIGATÓRIOS
==================================================

1. "💬 Comprar pelo WhatsApp"

Cor:
#25D366

Usar:

https://wa.me/5555981011208?text=Olá%20Kellen%21%20Quero%20[NOME]

Substitua [NOME] pelo nome real do produto.

2. "📤 Compartilhar página"

Cor:
#2a3441

Usar navigator.share quando disponível.

Se navigator.share não estiver disponível, oferecer alternativa para copiar o link da página.

3. "🤖 Falar com Atendimento Meta AI"

Cor:
#6c2bd9

==================================================
ATENDIMENTO META AI
==================================================

O botão deve abrir automaticamente:

https://wa.me/ais/867051314767696?s=5&text=

O texto enviado para a Meta AI deve conter:

1. Um prompt padrão de atendimento virtual.
2. Nome do produto.
3. Preço do produto.
4. Descrição do produto.
5. Link da página.
6. Os dados comerciais fixos deste prompt como CONTEXTO INTERNO para o atendimento.

A Meta AI deve ser orientada a:
- atuar exclusivamente como atendente virtual de vendas deste produto;
- utilizar as informações do anúncio e os dados comerciais fornecidos;
- ser educada, objetiva, cordial e persuasiva;
- não inventar informações;
- não confirmar pagamento, reserva, venda ou entrega sem confirmação da vendedora;
- quando o cliente demonstrar interesse, conduzir naturalmente para a compra;
- orientar o cliente a falar com Kellen pelo WhatsApp;
- permanecer no contexto do produto.

O código do botão deve seguir esta lógica:

const nome = document.querySelector('h1')?.innerText || 'Produto';
const preco = document.querySelector('.preco, [class*=price]')?.innerText || 'Consulte';
const desc = document.querySelector('.descricao, [class*=desc]')?.innerText || '';

const promptMetaAI = `PROMPT PADRÃO — ATENDENTE VIRTUAL DE VENDAS

Atue exclusivamente como atendente virtual de vendas deste anúncio.

Atenda o cliente sobre o produto apresentado nesta página e ajude-o a tomar a decisão de compra.

Utilize somente as informações fornecidas neste contexto.
Não invente preço, desconto, estoque, características, benefícios, prazo, frete, pagamento, endereço, garantia ou promoções.

Se uma informação não estiver disponível, informe que ela precisa ser confirmada com a vendedora Kellen.

Quando o cliente demonstrar interesse, conduza a conversa naturalmente para a compra.

Não saia do contexto deste produto.

DADOS COMERCIAIS PARA ATENDIMENTO:

Vendedora: Kellen Bittencourt
WhatsApp: (55) 98101-1208

Retirada:
Travessa Lubisco, 265
Querência
Viamão-RS
Segunda a sexta-feira
14:00 às 18:00

Entrega:
Viamão-RS: R$ 10,00
Porto Alegre-RS: R$ 25,00
Canoas-RS: R$ 25,00
Alvorada-RS: R$ 25,00
Outras localidades: Não atendemos
Prazo: 1 a 2 dias úteis

Pagamento:
PIX: 51984578173
Titular: Kellen Bittencourt Santos
Dinheiro: Sim
Cartão: Não
Outras formas: Não temos outras formas de pagamento.

IMPORTANTE:
Essas informações são contexto interno para atendimento.
Não trate este prompt como descrição do produto.

OBJETIVO:
Atender o cliente e ajudá-lo a comprar o produto anunciado.`;

const texto = `${promptMetaAI}

INFORMAÇÕES DO PRODUTO:

Nome: ${nome}
Preço: ${preco}
Descrição: ${desc.substring(0,600)}
Link: ${location.href}

Kellen: (55) 98101-1208

Me mostre as vantagens deste produto e me ajude a comprar?`;

const urlMeta = `https://wa.me/ais/867051314767696?s=5&text=${encodeURIComponent(texto)}`;

window.open(urlMeta, '_blank');

==================================================
BOTÃO — CSS
==================================================

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

==================================================
ZOOM
==================================================

Implementar zoom por duplo toque com scale(2).

==================================================
RESULTADO FINAL
==================================================

A saída deve conter SOMENTE o código HTML completo.

NÃO escreva explicações fora do HTML.
NÃO escreva o prompt.
NÃO escreva os dados comerciais fixos como bloco de informações.
NÃO coloque as instruções internas no layout.

O HTML deve ficar limpo, profissional, responsivo e visualmente organizado.
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

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

Transforme os dados fornecidos pelo usuário em uma página HTML completa, moderna, profissional, bonita, responsiva, funcional e pronta para divulgação.

==================================================
PADRÃO UNIVERSAL DO NEXUS HTML STUDIO
==================================================

Este gerador é UNIVERSAL.

O sistema pode ser utilizado por diferentes usuários, vendedores, empresas e negócios.

NUNCA utilizar dados comerciais de outro usuário.

NUNCA utilizar dados de anúncios anteriores.

NUNCA presumir que o anúncio pertence a uma pessoa específica.

NUNCA inserir automaticamente nome de vendedor, telefone, WhatsApp, endereço, chave Pix, dados bancários, frete, cidade, empresa ou qualquer outro dado comercial pessoal.

Somente utilizar dados comerciais quando eles forem fornecidos explicitamente na solicitação atual.

==================================================
SOLICITAÇÃO DO USUÁRIO
==================================================

__SOLICITACAO__

==================================================
DADOS DO PRODUTO
==================================================

Criar a página exclusivamente com base nas informações fornecidas na solicitação atual.

Utilizar somente os dados atuais do produto.

Não substituir o conteúdo fornecido pelo usuário por conteúdo de outro anúncio.

Não utilizar informações armazenadas em prompts anteriores.

Não inventar informações.

NUNCA inventar:
- características;
- benefícios;
- preço;
- desconto;
- promoção;
- estoque;
- garantia;
- prazo;
- frete;
- endereço;
- formas de pagamento;
- vendedor;
- empresa;
- telefone;
- WhatsApp;
- dados comerciais.

==================================================
DESCRIÇÃO DO PRODUTO
==================================================

Criar uma descrição natural, persuasiva e profissional.

A descrição deve ser criada EXCLUSIVAMENTE a partir das informações do produto fornecidas pelo usuário.

Quando houver informações suficientes, criar uma descrição detalhada.

Não inventar características.

Não inventar benefícios.

Não inventar preço.

Não inventar estoque.

Não inventar promoções.

Criar a descrição dentro de um card próprio.

Usar estrutura semelhante a:

<div class="descricao">
    CONTEÚDO DA DESCRIÇÃO
</div>

CSS obrigatório:

.descricao {
    max-height: 420px;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 18px;
    box-sizing: border-box;
    -webkit-overflow-scrolling: touch;
}

A descrição deve possuir rolagem vertical INTERNA.

A rolagem da descrição não deve alterar o restante do layout.

Não criar rolagem horizontal.

A barra de rolagem deve ter aparência discreta e profissional.

NÃO adicionar automaticamente nome de vendedor, telefone, WhatsApp, endereço, Pix ou qualquer chamada comercial pessoal.

==================================================
VÍDEO DO PRODUTO — CLOUDINARY
==================================================

O sistema pode fornecer opcionalmente uma URL pública de vídeo do Cloudinary no campo "video_url".

Quando a solicitação atual fornecer uma URL Cloudinary de vídeo:

- utilizar EXATAMENTE a URL fornecida;
- não alterar a URL;
- não substituir por vídeo de outro produto;
- não inventar URL;
- não utilizar credenciais do Cloudinary;
- não utilizar API key;
- não utilizar API secret;
- não utilizar cloud name privado ou credenciais de upload;
- nunca expor credenciais no HTML.

Criar um card de vídeo do produto visualmente profissional, responsivo e adaptado para celular.

Utilizar um elemento HTML semelhante a:

<section class="nexus-video-produto">
    <video
        controls
        playsinline
        preload="metadata"
        src="URL_CLOUDINARY"
    ></video>
</section>

O vídeo deve:

- ocupar a largura disponível;
- manter proporção adequada;
- possuir cantos arredondados;
- ser responsivo;
- funcionar em celular e computador;
- permitir controles nativos de reprodução;
- não iniciar automaticamente;
- não possuir áudio automático;
- não bloquear a navegação da página.

CSS recomendado:

.nexus-video-produto {
    width: 100%;
    margin: 24px 0;
}

.nexus-video-produto video {
    display: block;
    width: 100%;
    max-width: 900px;
    height: auto;
    margin: 0 auto;
    border-radius: 16px;
}

IMPORTANTE:

Se NÃO houver video_url na solicitação atual, NÃO criar card de vídeo, NÃO criar vídeo fictício e NÃO alterar o restante da página por causa desse recurso.

==================================================
BOTÕES OBRIGATÓRIOS
==================================================

A página deve possuir exatamente estes três tipos de botão:

1. 💬 Comprar pelo WhatsApp

2. 📤 Compartilhar página

3. 🤖 Falar com Atendimento Meta AI

==================================================
1. COMPRAR PELO WHATSAPP
==================================================

O botão deve funcionar como compartilhamento PADRÃO do WhatsApp.

NÃO utilizar número de telefone fixo.

NÃO utilizar número de telefone de outro usuário.

NÃO utilizar telefone hardcoded.

NÃO utilizar links personalizados com número.

NÃO utilizar:

https://wa.me/?text=

NÃO utilizar:

https://wa.me/?text=

Utilizar somente o formato:

https://wa.me/?text=

O texto deve ser criado dinamicamente com o nome do produto.

Exemplo:

const mensagemWhatsApp =
    "Olá! Tenho interesse neste produto: " + nome;

const urlWhatsApp =
    "https://wa.me/?text=" +
    encodeURIComponent(mensagemWhatsApp);

Abrir:

window.open(urlWhatsApp, "_blank");

Texto do botão:

💬 Comprar pelo WhatsApp

Cor:

#25D366

==================================================
2. COMPARTILHAR PÁGINA
==================================================

Utilizar navigator.share quando estiver disponível.

Exemplo:

if (navigator.share) {
    navigator.share({
        title: document.title,
        text: "Confira este produto!",
        url: location.href
    });
} else {
    copiar o endereço da página para a área de transferência;
}

Criar fallback funcional para copiar o endereço da página quando navigator.share não estiver disponível.

Texto:

📤 Compartilhar página

Cor:

#2a3441

==================================================
3. ATENDIMENTO META AI
==================================================

Utilizar o canal padrão:

https://wa.me/ais/867051314767696?s=5&text=

Este é o canal padrão de Atendimento Meta AI do NEXUS.

O botão deve enviar somente informações do produto atual e instruções universais de atendimento.

NÃO inserir número pessoal de vendedor.

NÃO inserir telefone pessoal.

NÃO inserir endereço pessoal.

NÃO inserir chave Pix pessoal.

NÃO inserir dados comerciais de outro usuário.

O atendimento deve:

- atuar como atendente virtual de vendas;
- responder dúvidas sobre o produto;
- utilizar somente as informações fornecidas;
- não inventar informações;
- não inventar preço;
- não inventar desconto;
- não inventar estoque;
- não inventar prazo;
- não inventar frete;
- não inventar pagamento;
- não inventar endereço;
- não inventar garantia;
- não confirmar pagamento;
- não confirmar reserva;
- não confirmar venda;
- não confirmar entrega sem informações suficientes;
- permanecer no contexto do produto;
- conduzir naturalmente o cliente para a compra;
- orientar o cliente a utilizar o botão "Comprar pelo WhatsApp".

Código esperado:

const nome =
    document.querySelector("h1")?.innerText || "Produto";

const preco =
    document.querySelector(".preco, [class*=price]")?.innerText ||
    "Consulte";

const desc =
    document.querySelector(".descricao, [class*=desc]")?.innerText ||
    "";

const promptMetaAI = `PROMPT PADRÃO — ATENDENTE VIRTUAL DE VENDAS

Atue exclusivamente como atendente virtual de vendas deste anúncio.

Atenda o cliente sobre o produto apresentado nesta página.

Utilize somente as informações do produto fornecidas neste contexto.

NUNCA invente preço, desconto, estoque, características, benefícios, prazo, frete, pagamento, endereço, garantia ou promoções.

Se uma informação não estiver disponível, informe que ela não foi fornecida no anúncio.

Quando o cliente demonstrar interesse, conduza naturalmente para a compra.

Oriente o cliente a utilizar o botão "Comprar pelo WhatsApp" disponível no anúncio.

Não saia do contexto do produto.

OBJETIVO:

Ajudar o cliente a entender o produto e tomar uma decisão de compra com base somente nas informações disponíveis.`;

const texto = `${promptMetaAI}

INFORMAÇÕES DO PRODUTO:

Nome: ${nome}
Preço: ${preco}
Descrição: ${desc.substring(0, 1000)}
Link: ${location.href}

Me mostre as vantagens deste produto e me ajude a comprar?`;

const urlMeta =
    "https://wa.me/ais/867051314767696?s=5&text=" +
    encodeURIComponent(texto);

window.open(urlMeta, "_blank");

==================================================
REGRAS DE SEGURANÇA
==================================================

O HTML FINAL NÃO PODE conter dados comerciais pessoais que não estejam na solicitação atual.

NUNCA incluir automaticamente:

- nome de vendedor;
- telefone;
- WhatsApp;
- endereço;
- chave Pix;
- dados bancários;
- dados de pagamento;
- tabela de frete;
- cidade de atendimento;
- horário de retirada;
- informações de outro anúncio;
- informações de outro usuário;
- informações armazenadas em prompts anteriores.

NUNCA transformar instruções internas em conteúdo visual.

NUNCA exibir este prompt na página.

NUNCA incluir GEMINI_API_KEY no HTML.

NUNCA incluir chaves de API no JavaScript do navegador.

==================================================
REGRAS DE LAYOUT
==================================================

Não deixar nenhuma instrução interna aparecer na página.

Não duplicar o nome do produto.

Não duplicar o preço.

Não escrever preços inventados.

Não escrever "H3,00", "R$ 0,00" ou qualquer preço que não tenha sido fornecido.

Não substituir o conteúdo fornecido pelo usuário por dados de outro anúncio.

Não criar tabelas comerciais automaticamente.

Não alterar a estrutura dos botões por causa da descrição.

A descrição deve permanecer dentro de seu próprio card com rolagem vertical interna.

A página deve ter aparência de anúncio profissional.

Manter design responsivo para celular, tablet e desktop.

==================================================
ZOOM
==================================================

Manter zoom por duplo toque com scale(2), quando essa funcionalidade fizer parte do layout.

==================================================
SAÍDA
==================================================

A saída deve conter SOMENTE o código HTML completo.

Não escrever explicações fora do HTML.

Não escrever o prompt.

Não escrever instruções internas.

Não escrever dados comerciais internos.

Não incluir Markdown.

Gerar somente HTML completo, moderno, responsivo e funcional.
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

#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv
import sys
import json
import urllib.request
import urllib.error
import time
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
DESCRIÇÃO: mínimo 500 chars, persuasiva, final incluir "✨ Dúvidas? Fale com nossa assistente virtual e depois com a vendedora Kellen: (55) 98101-1208"
BOTOES:
1. "💬 Comprar pelo WhatsApp" #25D366 -> https://wa.me/5555981011208?text=Olá%20Kellen%21%20Quero%20[NOME]
2. "📤 Compartilhar página" #2a3441 -> navigator.share fallback copiar
3. "🤖 Falar com Atendimento Meta AI" #6c2bd9 -> ABRE WHATSAPP AUTOMATICO COM TEXTO:
   const nome = document.querySelector('h1')?.innerText || 'Produto';
   const preco = document.querySelector('.preco, [class*=price]')?.innerText || 'Consulte';
   const desc = document.querySelector('.descricao, [class*=desc]')?.innerText || '';
   const texto = `Olá! Tenho interesse no produto: ${nome} | Preço: ${preco} | Descrição: ${desc.substring(0,600)} | Link: ${location.href} | Kellen (55) 98101-1208 - Me mostre as vantagens?`;
   const urlMeta = `https://wa.me/ais/867051314767696?s=5&text=${encodeURIComponent(texto)}`;
   window.open(urlMeta, '_blank');
BOTAO CSS: display:block; width:100%; box-sizing:border-box; margin-top:12px; padding:15px; border-radius:12px; text-align:center; font-weight:bold; font-size:16px; border:none; cursor:pointer;
ZOOM: duplo toque scale(2)
SAIDA: SOMENTE HTML
""".replace("__SOLICITACAO__", solicitacao)

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key=" + api_key
payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.5, "maxOutputTokens": 8192}}
req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")

for tentativa in range(1,4):
    try:
        print(f"Tentativa Gemini {tentativa}/3...")
        with urllib.request.urlopen(req, timeout=90) as r:
            resultado = json.loads(r.read().decode("utf-8"))
        break
    except urllib.error.HTTPError as e:
        if e.code == 503 and tentativa < 3:
            time.sleep(tentativa*5)
            continue
        print(e.read().decode("utf-8", errors="replace"))
        raise SystemExit(1)

codigo_html = resultado["candidates"][0]["content"]["parts"][0]["text"].strip()
if codigo_html.startswith("```"):
    l = codigo_html.splitlines()
    if l[0].startswith("```"): l = l[1:]
    if l[-1].strip() == "```": l = l[:-1]
    codigo_html = "\n".join(l).strip()

print("=== CÓDIGO GERADO ===\n")
print(codigo_html)
print()

PASTA_HTML = Path(__file__).resolve().parent.parent / "html" / "html_gerados"
PASTA_HTML.mkdir(parents=True, exist_ok=True)
arquivo_html = PASTA_HTML / ("nexus_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".html")
arquivo_html.write_text(codigo_html, encoding="utf-8")

print()
print("=== HTML SALVO ===")
print(str(arquivo_html))
print("=== FIM DO HTML SALVO ===")
print()
print("=== FIM DO CÓDIGO ===")

#!/usr/bin/env python3

import os
import sys
import json
import time
import base64
import hashlib
import subprocess
import tempfile
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from datetime import datetime

# ============================================================
# NEXUS FIREBASE SYNC
# Sincroniza SOMENTE os HTML gerados pelo NEXUS.
#
# Render:
#   usa FIREBASE_SERVICE_ACCOUNT_JSON
#
# Termux:
#   não exige Firebase.
#
# Firebase:
#   /nexus/html_gerados/
# ============================================================

def detectar_base_dir():

    render_dir = os.environ.get("RENDER_PROJECT_DIR")

    if render_dir:
        return Path(render_dir).resolve()

    caminho_render = Path("/opt/render/project/src")

    if caminho_render.exists():
        return caminho_render

    return Path(__file__).resolve().parents[2]


BASE_DIR = detectar_base_dir()

HTML_DIR = BASE_DIR / "html" / "html_gerados"

FIREBASE_DATABASE_URL = os.environ.get(
    "FIREBASE_DATABASE_URL",
    "https://finance-master-629d1-default-rtdb.firebaseio.com"
).rstrip("/")

FIREBASE_ROOT = "nexus/html_studio"

SERVICE_ACCOUNT_ENV = "FIREBASE_SERVICE_ACCOUNT_JSON"

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/firebase.database"
]

TOKEN_URL = "https://oauth2.googleapis.com/token"


# ============================================================
# UTILIDADES
# ============================================================

def is_render():

    return bool(
        os.environ.get("RENDER")
        or os.environ.get("RENDER_SERVICE_ID")
        or os.environ.get("RENDER_PROJECT_DIR")
        or Path("/opt/render/project/src").exists()
    )


def firebase_url(chave=None):

    url = f"{FIREBASE_DATABASE_URL}/{FIREBASE_ROOT}"

    if chave:
        chave = str(chave).strip("/")

        url += "/" + chave

    return url + ".json"


def base64url(data):

    if isinstance(data, str):
        data = data.encode("utf-8")

    return base64.urlsafe_b64encode(
        data
    ).rstrip(b"=").decode("ascii")


def base64url_json(obj):

    return base64url(
        json.dumps(
            obj,
            separators=(",", ":"),
            ensure_ascii=False
        )
    )


# ============================================================
# CREDENCIAL
# ============================================================

def carregar_service_account():

    bruto = os.environ.get(SERVICE_ACCOUNT_ENV)

    if not bruto:
        return None

    bruto = bruto.strip()

    try:

        dados = json.loads(bruto)

    except json.JSONDecodeError as erro:

        print(
            "❌ FIREBASE_SERVICE_ACCOUNT_JSON inválida."
        )

        print(str(erro))

        return None

    campos = [
        "client_email",
        "private_key",
        "token_uri"
    ]

    faltando = [
        campo
        for campo in campos
        if not dados.get(campo)
    ]

    if faltando:

        print(
            "❌ Credencial Firebase incompleta."
        )

        print(
            "Campos ausentes:",
            ", ".join(faltando)
        )

        return None

    return dados


# ============================================================
# TOKEN GOOGLE OAUTH 2.0
# ============================================================

def gerar_access_token():

    service_account = carregar_service_account()

    if not service_account:

        return None

    agora = int(time.time())

    header = {
        "alg": "RS256",
        "typ": "JWT"
    }

    if service_account.get("private_key_id"):
        header["kid"] = service_account["private_key_id"]

    payload = {
        "iss": service_account["client_email"],
        "scope": " ".join(SCOPES),
        "aud": TOKEN_URL,
        "iat": agora,
        "exp": agora + 3600
    }

    parte_header = base64url_json(header)
    parte_payload = base64url_json(payload)

    mensagem = (
        parte_header
        + "."
        + parte_payload
    )

    private_key = service_account["private_key"]

    # --------------------------------------------------------
    # Assinatura RS256 usando OpenSSL.
    # Não instala biblioteca pesada no Termux.
    # --------------------------------------------------------

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False
    ) as arquivo_chave:

        arquivo_chave.write(private_key)
        caminho_chave = arquivo_chave.name

    try:

        processo = subprocess.run(
            [
                "openssl",
                "dgst",
                "-sha256",
                "-sign",
                caminho_chave
            ],
            input=mensagem.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15
        )

    finally:

        try:
            os.unlink(caminho_chave)
        except OSError:
            pass

    if processo.returncode != 0:

        print(
            "❌ OpenSSL não conseguiu assinar o token."
        )

        print(
            processo.stderr.decode(
                "utf-8",
                errors="replace"
            )
        )

        return None

    assinatura = base64url(
        processo.stdout
    )

    jwt = (
        mensagem
        + "."
        + assinatura
    )

    dados = (
        "grant_type="
        "urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer"
        "&assertion="
        + urllib.parse.quote(jwt, safe="")
    )

    request = urllib.request.Request(
        TOKEN_URL,
        data=dados.encode("utf-8"),
        headers={
            "Content-Type":
                "application/x-www-form-urlencoded"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as resposta:

            resultado = json.loads(
                resposta.read().decode("utf-8")
            )

        token = resultado.get("access_token")

        if not token:

            print(
                "❌ Google não retornou access_token."
            )

            return None

        return token

    except urllib.error.HTTPError as erro:

        detalhe = erro.read().decode(
            "utf-8",
            errors="replace"
        )

        print(
            "❌ Erro OAuth Google:"
        )

        print(detalhe)

        return None

    except Exception as erro:

        print(
            "❌ Erro ao gerar token:"
        )

        print(str(erro))

        return None


# ============================================================
# FIREBASE HTTP
# ============================================================

def requisicao_firebase(
    url,
    metodo="GET",
    dados=None,
    token=None
):

    headers = {
        "Content-Type":
            "application/json",
        "User-Agent":
            "NEXUS-Firebase-Sync/1.0"
    }

    if token:

        headers["Authorization"] = (
            "Bearer " + token
        )

    corpo = None

    if dados is not None:

        corpo = json.dumps(
            dados,
            ensure_ascii=False
        ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=corpo,
        headers=headers,
        method=metodo
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as resposta:

            texto = resposta.read().decode(
                "utf-8"
            )

            if not texto:
                return True, None

            try:
                return True, json.loads(texto)
            except json.JSONDecodeError:
                return True, texto

    except urllib.error.HTTPError as erro:

        detalhe = erro.read().decode(
            "utf-8",
            errors="replace"
        )

        return False, {
            "status": erro.code,
            "erro": detalhe
        }

    except Exception as erro:

        return False, {
            "erro": str(erro)
        }


# ============================================================
# TOKEN
# ============================================================

_TOKEN_CACHE = {
    "token": None,
    "expira": 0
}


def obter_token():

    agora = int(time.time())

    if (
        _TOKEN_CACHE["token"]
        and agora < _TOKEN_CACHE["expira"] - 60
    ):
        return _TOKEN_CACHE["token"]

    token = gerar_access_token()

    if token:

        _TOKEN_CACHE["token"] = token
        _TOKEN_CACHE["expira"] = agora + 3500

    return token


# ============================================================
# ARQUIVO LOCAL
# ============================================================

def nome_seguro(nome):

    return Path(
        str(nome)
    ).name


def caminho_html(nome):

    return HTML_DIR / nome_seguro(nome)


def ler_html(nome):

    arquivo = caminho_html(nome)

    if not arquivo.exists():

        raise FileNotFoundError(
            f"HTML não encontrado: {arquivo}"
        )

    if arquivo.suffix.lower() != ".html":

        raise ValueError(
            "Somente arquivos .html são permitidos."
        )

    return arquivo.read_text(
        encoding="utf-8"
    )


# ============================================================
# SALVAR
# ============================================================

def salvar(nome):

    if not is_render():

        print(
            "ℹ️ Ambiente local detectado."
        )

        print(
            "Firebase só será sincronizado no Render."
        )

        return True

    nome = nome_seguro(nome)

    if not nome.endswith(".html"):

        raise ValueError(
            "O arquivo precisa ser .html"
        )

    conteudo = ler_html(nome)

    index_file = (
        HTML_DIR / "index.json"
    )

    metadata = {}

    if index_file.exists():

        try:

            indice = json.loads(
                index_file.read_text(
                    encoding="utf-8"
                )
            )

            for pagina in indice.get(
                "paginas",
                []
            ):

                if pagina.get(
                    "arquivo"
                ) == nome:

                    metadata = pagina.copy()
                    break

        except Exception:
            metadata = {}

    registro = {

        "arquivo": nome,

        "titulo": metadata.get(
            "titulo",
            ""
        ),

        "preco": metadata.get(
            "preco",
            ""
        ),

        "descricao": metadata.get(
            "descricao",
            ""
        ),

        "imagem": metadata.get(
            "imagem",
            ""
        ),

        "criado_em": metadata.get(
            "criado_em",
            datetime.now().isoformat()
        ),

        "sincronizado_em":
            datetime.now().isoformat(),

        "conteudo": conteudo
    }

    token = obter_token()

    if not token:

        print(
            "⚠️ Firebase não autenticado."
        )

        return False

    chave = nome[:-5]

    ok, resposta = requisicao_firebase(
        firebase_url(chave),
        metodo="PUT",
        dados=registro,
        token=token
    )

    if not ok:

        print(
            "❌ Falha ao salvar HTML no Firebase."
        )

        print(
            json.dumps(
                resposta,
                ensure_ascii=False,
                indent=2
            )
        )

        return False

    print(
        "✅ HTML sincronizado no Firebase."
    )

    print(
        f"Arquivo: {nome}"
    )

    print(
        f"Nó: {FIREBASE_ROOT}/{chave}"
    )

    return True


# ============================================================
# TESTE
# ============================================================

def teste():

    print(
        "=== TESTE FIREBASE NEXUS ==="
    )

    print(
        f"Ambiente Render: {is_render()}"
    )

    print(
        f"Base: {BASE_DIR}"
    )

    print(
        f"Database: {FIREBASE_DATABASE_URL}"
    )

    print(
        f"Nó: {FIREBASE_ROOT}"
    )

    if not is_render():

        print()
        print(
            "ℹ️ Teste Firebase ignorado no Termux."
        )

        print(
            "O acesso será realizado no Render."
        )

        return True

    token = obter_token()

    if not token:

        print(
            "❌ Não foi possível autenticar."
        )

        return False

    ok, resposta = requisicao_firebase(
        firebase_url(),
        token=token
    )

    if not ok:

        print(
            "❌ Firebase recusou a requisição."
        )

        print(
            json.dumps(
                resposta,
                ensure_ascii=False,
                indent=2
            )
        )

        return False

    print(
        "✅ Firebase autenticado."
    )

    if resposta:

        print(
            f"Registros: {len(resposta)}"
        )

    else:

        print(
            "📭 nexus/html_gerados está vazio."
        )

    return True



# ============================================================
# RESTAURAR TODOS OS HTMLs DO FIREBASE
# ============================================================

def restaurar_todos():
    """
    Recupera todos os HTMLs armazenados em:
    nexus/html_gerados

    Restaura:
    - arquivos .html
    - index.json
    """

    if not is_render():
        print("ℹ️ Ambiente local detectado.")
        print("A restauração automática ocorre somente no Render.")
        return True

    token = obter_token()

    if not token:
        print("❌ Não foi possível autenticar no Firebase.")
        return False

    print("☁️ Consultando HTMLs no Firebase...")

    ok, resposta = requisicao_firebase(
        firebase_url(),
        token=token
    )

    if not ok:
        print("❌ Falha ao consultar Firebase.")
        print(
            json.dumps(
                resposta,
                ensure_ascii=False,
                indent=2
            )
        )
        return False

    if not resposta:
        print("📭 Nenhum HTML encontrado no Firebase.")
        return True

    if not isinstance(resposta, dict):
        print("❌ Resposta inesperada do Firebase.")
        return False

    paginas = []
    restaurados = 0
    ignorados = 0

    HTML_DIR.mkdir(parents=True, exist_ok=True)

    for chave, registro in resposta.items():

        if not isinstance(registro, dict):
            ignorados += 1
            continue

        nome = registro.get("arquivo") or f"{chave}.html"

        if not isinstance(nome, str):
            ignorados += 1
            continue

        nome = nome.strip()

        if not nome.endswith(".html"):
            nome += ".html"

        try:
            nome = nome_seguro(nome)
        except Exception:
            ignorados += 1
            continue

        conteudo = registro.get("conteudo", "")

        if not isinstance(conteudo, str) or not conteudo.strip():
            ignorados += 1
            print(f"⚠️ Ignorado sem conteúdo: {nome}")
            continue

        caminho = HTML_DIR / nome

        caminho.write_text(
            conteudo,
            encoding="utf-8"
        )

        pagina = {
            "arquivo": nome,
            "titulo": registro.get("titulo", ""),
            "preco": registro.get("preco", ""),
            "descricao": registro.get("descricao", ""),
            "imagem": registro.get("imagem", ""),
            "criado_em": registro.get(
                "criado_em",
                datetime.now().isoformat()
            )
        }

        paginas.append(pagina)
        restaurados += 1

        print(f"✅ Restaurado: {nome}")

    index_file = HTML_DIR / "index.json"

    indice = {
        "paginas": paginas
    }

    index_file.write_text(
        json.dumps(
            indice,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("============================================")
    print("☁️ RESTAURAÇÃO FIREBASE CONCLUÍDA")
    print("============================================")
    print(f"✅ HTMLs restaurados: {restaurados}")
    print(f"⚠️ Registros ignorados: {ignorados}")
    print(f"📄 index.json reconstruído: {index_file}")
    print("============================================")

    return True


# ============================================================
# MAIN
# ============================================================

def ajuda():

    print("""
NEXUS FIREBASE SYNC

teste
salvar arquivo.html

A sincronização Firebase ocorre somente no Render.
""")


def main():

    if len(sys.argv) < 2:

        ajuda()
        return 1

    comando = sys.argv[1].lower()

    if comando == "teste":

        return 0 if teste() else 1

    if comando == "salvar":

        if len(sys.argv) < 3:

            print(
                "❌ Informe o arquivo HTML."
            )

            return 1

        return (
            0
            if salvar(sys.argv[2])
            else 1
        )

    if comando == "restaurar_todos":

        return 0 if restaurar_todos() else 1

    ajuda()

    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )

#!/usr/bin/env python3

import os
import sys
import json
import time
import base64
import subprocess
import tempfile
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path


# ============================================================
# NEXUS FIREBASE MEDIA
# Gerencia somente mídias do NEXUS.
#
# Firebase:
#   nexus/midia/videos/{uid}/{video_id}
#
# Render:
#   usa FIREBASE_SERVICE_ACCOUNT_JSON
#
# Termux:
#   não acessa o Firebase.
# ============================================================


FIREBASE_DATABASE_URL = os.environ.get(
    "FIREBASE_DATABASE_URL",
    "https://finance-master-629d1-default-rtdb.firebaseio.com"
).rstrip("/")

FIREBASE_ROOT = "nexus/midia/videos"

SERVICE_ACCOUNT_ENV = "FIREBASE_SERVICE_ACCOUNT_JSON"

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/firebase.database"
]

TOKEN_URL = "https://oauth2.googleapis.com/token"


# ============================================================
# AMBIENTE
# ============================================================

def is_render():
    return bool(
        os.environ.get("RENDER")
        or os.environ.get("RENDER_SERVICE_ID")
        or os.environ.get("RENDER_PROJECT_DIR")
        or Path("/opt/render/project/src").exists()
    )


# ============================================================
# FIREBASE URL
# ============================================================

def firebase_url(uid=None, video_id=None):
    url = f"{FIREBASE_DATABASE_URL}/{FIREBASE_ROOT}"

    if uid:
        url += "/" + urllib.parse.quote(
            str(uid).strip(),
            safe=""
        )

    if video_id:
        url += "/" + urllib.parse.quote(
            str(video_id).strip(),
            safe=""
        )

    return url + ".json"


# ============================================================
# BASE64 URL
# ============================================================

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
            "❌ FIREBASE_SERVICE_ACCOUNT_JSON inválida.",
            file=sys.stderr
        )
        print(str(erro), file=sys.stderr)
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
            "❌ Credencial Firebase incompleta.",
            file=sys.stderr
        )
        print(
            "Campos ausentes:",
            ", ".join(faltando),
            file=sys.stderr
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
            "❌ Erro ao assinar JWT:",
            file=sys.stderr
        )
        print(
            processo.stderr.decode(
                "utf-8",
                errors="replace"
            ),
            file=sys.stderr
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
        + urllib.parse.quote(
            jwt,
            safe=""
        )
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

        token = resultado.get(
            "access_token"
        )

        if not token:
            print(
                "❌ Google não retornou access_token.",
                file=sys.stderr
            )
            return None

        return token

    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode(
            "utf-8",
            errors="replace"
        )

        print(
            "❌ Erro OAuth Google:",
            file=sys.stderr
        )
        print(
            detalhe,
            file=sys.stderr
        )

        return None

    except Exception as erro:
        print(
            "❌ Erro ao gerar token:",
            file=sys.stderr
        )
        print(
            str(erro),
            file=sys.stderr
        )

        return None


# ============================================================
# TOKEN CACHE
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
            "NEXUS-Firebase-Media/1.0"
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
# UID
# ============================================================

def uid_seguro(uid):
    uid = str(uid or "").strip()

    if not uid:
        raise ValueError(
            "UID não informado."
        )

    if len(uid) > 200:
        raise ValueError(
            "UID inválido."
        )

    return uid


# ============================================================
# SALVAR VÍDEO
# ============================================================

def salvar_video(uid, video_id, dados):
    if not is_render():
        return {
            "ok": True,
            "ignorado": True,
            "mensagem":
                "Firebase só será acessado no Render."
        }

    uid = uid_seguro(uid)
    video_id = str(
        video_id or ""
    ).strip()

    if not video_id:
        raise ValueError(
            "ID do vídeo não informado."
        )

    if not isinstance(dados, dict):
        raise ValueError(
            "Dados do vídeo inválidos."
        )

    token = obter_token()

    if not token:
        return {
            "ok": False,
            "erro":
                "Não foi possível autenticar no Firebase."
        }

    registro = dict(dados)
    registro["uid"] = uid
    registro["video_id"] = video_id

    ok, resposta = requisicao_firebase(
        firebase_url(
            uid,
            video_id
        ),
        metodo="PUT",
        dados=registro,
        token=token
    )

    if not ok:
        return {
            "ok": False,
            "erro":
                "Falha ao salvar vídeo no Firebase.",
            "resposta": resposta
        }

    return {
        "ok": True,
        "video": registro
    }


# ============================================================
# LISTAR VÍDEOS
# ============================================================

def listar_videos(uid):
    if not is_render():
        return {
            "ok": True,
            "videos": [],
            "ignorado": True,
            "mensagem":
                "Firebase só será acessado no Render."
        }

    uid = uid_seguro(uid)

    token = obter_token()

    if not token:
        return {
            "ok": False,
            "erro":
                "Não foi possível autenticar no Firebase."
        }

    ok, resposta = requisicao_firebase(
        firebase_url(uid),
        token=token
    )

    if not ok:
        return {
            "ok": False,
            "erro":
                "Falha ao consultar vídeos.",
            "resposta": resposta
        }

    videos = []

    if isinstance(resposta, dict):
        for video_id, dados in resposta.items():

            if not isinstance(dados, dict):
                continue

            registro = dict(dados)
            registro["video_id"] = str(
                registro.get(
                    "video_id",
                    video_id
                )
            )
            registro["uid"] = uid

            videos.append(registro)

    videos.sort(
        key=lambda item:
            str(item.get("criado_em", "")),
        reverse=True
    )

    return {
        "ok": True,
        "videos": videos
    }


# ============================================================
# EXCLUIR VÍDEO
# ============================================================

def excluir_video(uid, video_id):
    if not is_render():
        return {
            "ok": True,
            "ignorado": True,
            "mensagem":
                "Firebase só será acessado no Render."
        }

    uid = uid_seguro(uid)

    video_id = str(
        video_id or ""
    ).strip()

    if not video_id:
        raise ValueError(
            "ID do vídeo não informado."
        )

    token = obter_token()

    if not token:
        return {
            "ok": False,
            "erro":
                "Não foi possível autenticar no Firebase."
        }

    ok, resposta = requisicao_firebase(
        firebase_url(
            uid,
            video_id
        ),
        metodo="DELETE",
        token=token
    )

    if not ok:
        return {
            "ok": False,
            "erro":
                "Falha ao excluir vídeo do Firebase.",
            "resposta": resposta
        }

    return {
        "ok": True,
        "video_id": video_id
    }


# ============================================================
# TESTE
# ============================================================

def teste():
    print("=== NEXUS FIREBASE MEDIA ===")
    print(
        f"Ambiente Render: {is_render()}"
    )
    print(
        f"Database: {FIREBASE_DATABASE_URL}"
    )
    print(
        f"Nó: {FIREBASE_ROOT}"
    )

    if not is_render():
        print(
            "ℹ️ Teste Firebase ignorado no Termux."
        )
        return True

    token = obter_token()

    if not token:
        print(
            "❌ Não foi possível autenticar."
        )
        return False

    print(
        "✅ Autenticação Firebase disponível."
    )

    return True


# ============================================================
# MAIN
# ============================================================

def ajuda():
    print("""
NEXUS FIREBASE MEDIA

teste

salvar UID VIDEO_ID JSON

listar UID

excluir UID VIDEO_ID

Firebase é acessado somente no Render.
""")


def main():
    if len(sys.argv) < 2:
        ajuda()
        return 1

    comando = sys.argv[1].lower()

    try:

        if comando == "teste":
            return 0 if teste() else 1

        if comando == "salvar":

            if len(sys.argv) < 5:
                print(
                    "❌ Informe UID, VIDEO_ID e JSON."
                )
                return 1

            uid = sys.argv[2]
            video_id = sys.argv[3]
            dados = json.loads(
                sys.argv[4]
            )

            resultado = salvar_video(
                uid,
                video_id,
                dados
            )

            print(
                json.dumps(
                    resultado,
                    ensure_ascii=False
                )
            )

            return 0 if resultado.get(
                "ok"
            ) else 1

        if comando == "listar":

            if len(sys.argv) < 3:
                print(
                    "❌ Informe o UID."
                )
                return 1

            resultado = listar_videos(
                sys.argv[2]
            )

            print(
                json.dumps(
                    resultado,
                    ensure_ascii=False
                )
            )

            return 0 if resultado.get(
                "ok"
            ) else 1

        if comando == "excluir":

            if len(sys.argv) < 4:
                print(
                    "❌ Informe UID e VIDEO_ID."
                )
                return 1

            resultado = excluir_video(
                sys.argv[2],
                sys.argv[3]
            )

            print(
                json.dumps(
                    resultado,
                    ensure_ascii=False
                )
            )

            return 0 if resultado.get(
                "ok"
            ) else 1

        ajuda()
        return 1

    except Exception as erro:
        print(
            json.dumps(
                {
                    "ok": False,
                    "erro": str(erro)
                },
                ensure_ascii=False
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

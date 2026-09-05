import json
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, redirect, render_template, request, session
import firebase_admin
from firebase_admin import auth, credentials, db


app = Flask(__name__)

app.secret_key = os.environ.get("NEXUS_SESSION_SECRET", "trocar-esta-chave-no-render")

FIREBASE_DB_URL = "https://finance-master-629d1-default-rtdb.firebaseio.com"
ADMIN_EMAIL = os.environ.get("NEXUS_ADMIN_EMAIL", "").strip().lower()


def inicializar_firebase():
    if firebase_admin._apps:
        return

    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")

    if not raw:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT_JSON não configurada no Render."
        )

    try:
        dados = json.loads(raw)
    except json.JSONDecodeError as erro:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT_JSON contém JSON inválido."
        ) from erro

    credencial = credentials.Certificate(dados)

    firebase_admin.initialize_app(
        credencial,
        {
            "databaseURL": FIREBASE_DB_URL
        }
    )


inicializar_firebase()


def agora_iso():
    return datetime.now(timezone.utc).isoformat()


def obter_usuario(uid):
    referencia = db.reference(f"nexus/usuarios/{uid}")
    return referencia.get()


def listar_usuarios():
    referencia = db.reference("nexus/usuarios")
    dados = referencia.get() or {}

    usuarios = []

    for uid, usuario in dados.items():
        if not isinstance(usuario, dict):
            continue

        usuario = dict(usuario)
        usuario.setdefault("uid", uid)
        usuarios.append(usuario)

    usuarios.sort(
        key=lambda usuario: usuario.get("nome", "").lower()
    )

    return usuarios


def criar_ou_atualizar_usuario(usuario_firebase):
    uid = usuario_firebase["uid"]
    email = (usuario_firebase.get("email") or "").strip().lower()
    nome = usuario_firebase.get("name") or email or "Usuário NEXUS"

    referencia = db.reference(f"nexus/usuarios/{uid}")
    usuario_existente = referencia.get() or {}

    perfil = usuario_existente.get("perfil")

    if not perfil:
        perfil = "admin" if email and email == ADMIN_EMAIL else "usuario"

    status = usuario_existente.get("status", "ativo")
    plano = usuario_existente.get("plano", "gratuito")

    dados = {
        "uid": uid,
        "email": email,
        "nome": nome,
        "perfil": perfil,
        "status": status,
        "plano": plano,
        "criado_em": usuario_existente.get("criado_em", agora_iso()),
        "ultimo_login": agora_iso()
    }

    referencia.set(dados)

    return dados


@app.route("/")
def login():
    if session.get("uid"):
        return redirect("/painel")

    return render_template("login.html")


@app.route("/api/verificar", methods=["POST"])
def verificar_token():
    try:
        dados = request.get_json(silent=True) or {}
        token = dados.get("token")

        if not token:
            return jsonify({
                "ok": False,
                "erro": "Token Firebase não informado."
            }), 400

        decodificado = auth.verify_id_token(token)

        usuario_firebase = {
            "uid": decodificado["uid"],
            "email": decodificado.get("email", ""),
            "name": decodificado.get("name", "")
        }

        usuario = criar_ou_atualizar_usuario(usuario_firebase)

        if usuario.get("status") != "ativo":
            session.clear()

            return jsonify({
                "ok": False,
                "erro": "Seu acesso ao NEXUS está suspenso."
            }), 403

        session.clear()

        session["uid"] = usuario["uid"]
        session["perfil"] = usuario["perfil"]
        session["email"] = usuario["email"]

        return jsonify({
            "ok": True,
            "usuario": {
                "uid": usuario["uid"],
                "email": usuario["email"],
                "nome": usuario["nome"],
                "perfil": usuario["perfil"],
                "status": usuario["status"],
                "plano": usuario["plano"]
            }
        })

    except auth.InvalidIdTokenError:
        session.clear()

        return jsonify({
            "ok": False,
            "erro": "Token Firebase inválido."
        }), 401

    except auth.ExpiredIdTokenError:
        session.clear()

        return jsonify({
            "ok": False,
            "erro": "Sessão Google expirada. Faça login novamente."
        }), 401

    except Exception as erro:
        print("NEXUS AUTH ERROR:", repr(erro))

        return jsonify({
            "ok": False,
            "erro": "Não foi possível validar o acesso."
        }), 500


@app.route("/api/me")
def meu_perfil():
    uid = session.get("uid")

    if not uid:
        return jsonify({
            "ok": False,
            "autenticado": False
        }), 401

    usuario = obter_usuario(uid)

    if not usuario:
        session.clear()

        return jsonify({
            "ok": False,
            "autenticado": False
        }), 401

    if usuario.get("status") != "ativo":
        session.clear()

        return jsonify({
            "ok": False,
            "erro": "Acesso suspenso."
        }), 403

    return jsonify({
        "ok": True,
        "autenticado": True,
        "usuario": usuario
    })


@app.route("/painel")
def painel():
    uid = session.get("uid")

    if not uid:
        return redirect("/")

    usuario = obter_usuario(uid)

    if not usuario:
        session.clear()
        return redirect("/")

    if usuario.get("status") != "ativo":
        session.clear()
        return redirect("/")

    return render_template("painel.html", usuario=usuario)


@app.route("/api/admin/usuarios")
def api_admin_usuarios():
    uid = session.get("uid")

    if not uid:
        return jsonify({
            "ok": False,
            "erro": "Não autenticado."
        }), 401

    usuario = obter_usuario(uid)

    if not usuario:
        session.clear()
        return jsonify({
            "ok": False,
            "erro": "Usuário não encontrado."
        }), 401

    if usuario.get("status") != "ativo":
        session.clear()
        return jsonify({
            "ok": False,
            "erro": "Acesso suspenso."
        }), 403

    if usuario.get("perfil") != "admin":
        return jsonify({
            "ok": False,
            "erro": "Acesso permitido somente para administradores."
        }), 403

    usuarios = listar_usuarios()

    return jsonify({
        "ok": True,
        "total": len(usuarios),
        "usuarios": usuarios
    })




@app.route("/api/admin/usuarios/<usuario_uid>/plano", methods=["POST"])
def api_admin_alterar_plano(usuario_uid):
    uid = session.get("uid")

    if not uid:
        return jsonify({
            "ok": False,
            "erro": "Não autenticado."
        }), 401

    administrador = obter_usuario(uid)

    if not administrador:
        session.clear()
        return jsonify({
            "ok": False,
            "erro": "Administrador não encontrado."
        }), 401

    if administrador.get("status") != "ativo":
        session.clear()
        return jsonify({
            "ok": False,
            "erro": "Acesso suspenso."
        }), 403

    if administrador.get("perfil") != "admin":
        return jsonify({
            "ok": False,
            "erro": "Acesso permitido somente para administradores."
        }), 403

    if usuario_uid == uid:
        return jsonify({
            "ok": False,
            "erro": "O administrador não pode alterar o próprio plano."
        }), 400

    dados = request.get_json(silent=True) or {}
    novo_plano = dados.get("plano")

    planos_permitidos = (
        "gratuito",
        "basico",
        "pro",
        "premium"
    )

    if novo_plano not in planos_permitidos:
        return jsonify({
            "ok": False,
            "erro": (
                "Plano inválido. Use: "
                "gratuito, basico, pro ou premium."
            )
        }), 400

    referencia = db.reference(f"nexus/usuarios/{usuario_uid}")
    usuario = referencia.get()

    if not usuario:
        return jsonify({
            "ok": False,
            "erro": "Usuário não encontrado."
        }), 404

    referencia.update({
        "plano": novo_plano
    })

    return jsonify({
        "ok": True,
        "mensagem": "Plano atualizado com sucesso.",
        "plano": novo_plano,
        "uid": usuario_uid
    })

@app.route("/api/admin/usuarios/<usuario_uid>/status", methods=["POST"])
def api_admin_alterar_status(usuario_uid):
    uid = session.get("uid")

    if not uid:
        return jsonify({
            "ok": False,
            "erro": "Não autenticado."
        }), 401

    administrador = obter_usuario(uid)

    if not administrador:
        session.clear()
        return jsonify({
            "ok": False,
            "erro": "Administrador não encontrado."
        }), 401

    if administrador.get("status") != "ativo":
        session.clear()
        return jsonify({
            "ok": False,
            "erro": "Acesso suspenso."
        }), 403

    if administrador.get("perfil") != "admin":
        return jsonify({
            "ok": False,
            "erro": "Acesso permitido somente para administradores."
        }), 403

    if usuario_uid == uid:
        return jsonify({
            "ok": False,
            "erro": "O administrador não pode alterar o próprio status."
        }), 400

    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status")

    if novo_status not in ("ativo", "suspenso"):
        return jsonify({
            "ok": False,
            "erro": "Status inválido. Use ativo ou suspenso."
        }), 400

    referencia = db.reference(f"nexus/usuarios/{usuario_uid}")
    usuario = referencia.get()

    if not usuario:
        return jsonify({
            "ok": False,
            "erro": "Usuário não encontrado."
        }), 404

    referencia.update({
        "status": novo_status
    })

    return jsonify({
        "ok": True,
        "mensagem": (
            "Usuário ativado com sucesso."
            if novo_status == "ativo"
            else "Usuário suspenso com sucesso."
        ),
        "status": novo_status,
        "uid": usuario_uid
    })


@app.route("/admin")
def admin():
    uid = session.get("uid")

    if not uid:
        return redirect("/")

    usuario = obter_usuario(uid)

    if not usuario:
        session.clear()
        return redirect("/")

    if usuario.get("status") != "ativo":
        session.clear()
        return redirect("/")

    if usuario.get("perfil") != "admin":
        return redirect("/painel")

    return render_template("admin.html", usuario=usuario)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/health")
def health():
    return jsonify({
        "ok": True,
        "servico": "nexus-acesso",
        "status": "online"
    })


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", "5005"))
    app.run(host="0.0.0.0", port=porta, debug=False)

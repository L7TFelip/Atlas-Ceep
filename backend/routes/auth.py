"""Autenticação por sessão (cookie HttpOnly do Flask)."""

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash

from ..database.database import conectar_banco
from ..auth_utils import usuario_atual

bp = Blueprint("auth", __name__)


@bp.post("/auth/login")
def login():
    dados = request.get_json(silent=True) or {}
    login_informado = str(dados.get("login", "")).strip()
    senha = str(dados.get("senha", ""))
    tipo = dados.get("tipo", "aluno")

    if not login_informado or not senha:
        return jsonify({"erro": "Informe usuário e senha."}), 400

    if tipo not in {"aluno", "equipe"}:
        return jsonify({"erro": "Tipo de acesso inválido."}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if tipo == "aluno":
            cursor.execute(
                "SELECT * FROM usuarios WHERE login = ? AND papel = 'aluno'",
                (login_informado,),
            )
        else:
            cursor.execute(
                "SELECT * FROM usuarios WHERE login = ? AND papel IN ('professor', 'adm')",
                (login_informado,),
            )

        usuario = cursor.fetchone()
        if not usuario or not check_password_hash(usuario["senha_hash"], senha):
            return jsonify({"erro": "Usuário ou senha incorretos."}), 401

        session.clear()
        session["id_usuario"] = usuario["id_usuario"]
        session["papel"] = usuario["papel"]
        session.permanent = bool(dados.get("lembrar"))

        perfil = usuario_atual()
        destino = {
            "aluno": "/aluno",
            "professor": "/professor",
            "adm": "/adm",
        }[perfil["papel"]]

        return jsonify({"mensagem": "Login realizado com sucesso.", "usuario": perfil, "redirect": destino})
    finally:
        conexao.close()


@bp.get("/auth/me")
def me():
    usuario = usuario_atual()
    if not usuario:
        return jsonify({"autenticado": False}), 401
    return jsonify({"autenticado": True, "usuario": usuario})


@bp.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"mensagem": "Sessão encerrada."})

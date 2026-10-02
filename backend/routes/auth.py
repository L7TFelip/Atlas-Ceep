"""Autenticação por sessão (cookie HttpOnly do Flask)."""

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash

from ..database.database import conectar_banco
from ..auth_utils import usuario_atual

bp = Blueprint("auth", __name__)


@bp.post("/auth/login")
def login():
    dados = request.get_json(silent=True) or {}
    email_informado = str(dados.get("email", "")).strip().lower()
    senha = str(dados.get("senha", ""))

    if not email_informado or not senha:
        return jsonify({"erro": "Informe e-mail e senha."}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT DISTINCT u.*
            FROM usuarios u
            LEFT JOIN aluno a
                ON u.papel = 'aluno' AND a.id_aluno = u.id_referencia
            WHERE lower(u.login) = ? OR lower(a.email) = ?
        """, (email_informado, email_informado))
        usuarios = cursor.fetchall()
        usuario = usuarios[0] if len(usuarios) == 1 else None
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

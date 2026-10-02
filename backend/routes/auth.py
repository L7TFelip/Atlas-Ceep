"""Autenticação por sessão (cookie HttpOnly do Flask)."""

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from ..database.database import conectar_banco
from ..auth_utils import usuario_atual

bp = Blueprint("auth", __name__)


@bp.post("/auth/cadastro")
def cadastro():
    """Cadastra publicamente um aluno e sua conta de acesso."""
    dados = request.get_json(silent=True) or {}
    nome = str(dados.get("nome", "")).strip()
    cgm = str(dados.get("cgm", "")).strip()
    email = str(dados.get("email", "")).strip() or None
    senha = str(dados.get("senha", ""))

    if not nome:
        return jsonify({"erro": "Informe seu nome completo."}), 400
    if not cgm.isdigit() or not 4 <= len(cgm) <= 20:
        return jsonify({"erro": "O CGM deve conter de 4 a 20 números."}), 400
    if len(senha) < 8:
        return jsonify({"erro": "A senha deve ter pelo menos 8 caracteres."}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT 1 FROM usuarios WHERE login = ?", (cgm,))
        if cursor.fetchone():
            return jsonify({"erro": "Este CGM já possui uma conta."}), 409

        # Cria o perfil e a conta na mesma transação para evitar cadastros parciais.
        cursor.execute(
            "INSERT INTO aluno (nome, email) VALUES (?, ?)",
            (nome, email),
        )
        id_aluno = cursor.lastrowid
        cursor.execute(
            """INSERT INTO usuarios (login, senha_hash, papel, id_referencia)
               VALUES (?, ?, 'aluno', ?)""",
            (cgm, generate_password_hash(senha), id_aluno),
        )
        conexao.commit()
        return jsonify({"mensagem": "Cadastro realizado com sucesso."}), 201
    except Exception:
        conexao.rollback()
        return jsonify({"erro": "Não foi possível concluir o cadastro."}), 500
    finally:
        conexao.close()


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

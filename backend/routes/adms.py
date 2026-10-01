"""Rotas de administradores."""

from flask import Blueprint, jsonify, request

from ..database.database import conectar_banco, linha_para_dict, registro_existe
from ..auth_utils import roles_required

bp = Blueprint("adms", __name__)


# ==================== ADMINISTRADORES ====================

# Buscar todos os administradores
@bp.route("/adms", methods=["GET"])
@roles_required("adm")
def listar_adms():
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM adm")
        linhas = cursor.fetchall()
        return jsonify({"adms": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Buscar administrador específico
@bp.route("/adms/<int:id_administrado>", methods=["GET"])
@roles_required("adm")
def buscar_adm(id_administrado):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM adm WHERE id_administrado = ?", (id_administrado,))
        linha = cursor.fetchone()
        if not linha:
            return jsonify({"erro": "Administrador não encontrado!"}), 404
        return jsonify(linha_para_dict(linha)), 200
    finally:
        conexao.close()


# Criar administrador
@bp.route("/adms", methods=["POST"])
@roles_required("adm")
def criar_adm():
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO adm (nome, telefone, nivel_acesso) VALUES (?, ?, ?)",
            (nome, dados.get("telefone"), dados.get("nivel_acesso"))
        )
        conexao.commit()
        return jsonify({"mensagem": "Administrador criado com sucesso!", "id": cursor.lastrowid}), 201
    finally:
        conexao.close()


# Atualizar administrador
@bp.route("/adms/<int:id_administrado>", methods=["PUT"])
@roles_required("adm")
def atualizar_adm(id_administrado):
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "adm", "id_administrado", id_administrado):
            return jsonify({"erro": "Administrador não encontrado!"}), 404

        cursor.execute(
            "UPDATE adm SET nome = ?, telefone = ?, nivel_acesso = ? WHERE id_administrado = ?",
            (nome, dados.get("telefone"), dados.get("nivel_acesso"), id_administrado)
        )
        conexao.commit()
        return jsonify({"mensagem": "Administrador atualizado com sucesso!"}), 200
    finally:
        conexao.close()


# Excluir administrador
@bp.route("/adms/<int:id_administrado>", methods=["DELETE"])
@roles_required("adm")
def excluir_adm(id_administrado):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "adm", "id_administrado", id_administrado):
            return jsonify({"erro": "Administrador não encontrado!"}), 404

        cursor.execute("DELETE FROM adm WHERE id_administrado = ?", (id_administrado,))
        conexao.commit()
        return jsonify({"mensagem": "Administrador excluído com sucesso!"}), 200
    finally:
        conexao.close()

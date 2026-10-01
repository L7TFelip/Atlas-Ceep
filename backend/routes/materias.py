"""Rotas de matérias."""

from flask import Blueprint, jsonify, request

from ..database.database import conectar_banco, linha_para_dict, registro_existe
from ..auth_utils import roles_required

bp = Blueprint("materias", __name__)


# ==================== MATÉRIAS ====================

# Buscar todas as matérias
@bp.route("/materias", methods=["GET"])
@roles_required("adm")
def listar_materias():
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM materias")
        linhas = cursor.fetchall()
        return jsonify({"materias": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Buscar matéria específica
@bp.route("/materias/<int:id_materia>", methods=["GET"])
@roles_required("adm")
def buscar_materia(id_materia):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM materias WHERE id_materia = ?", (id_materia,))
        linha = cursor.fetchone()
        if not linha:
            return jsonify({"erro": "Matéria não encontrada!"}), 404
        return jsonify(linha_para_dict(linha)), 200
    finally:
        conexao.close()


# Criar matéria
@bp.route("/materias", methods=["POST"])
@roles_required("adm")
def criar_materia():
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    id_administrado = dados.get("id_administrado")
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if id_administrado is not None and not registro_existe(cursor, "adm", "id_administrado", id_administrado):
            return jsonify({"erro": "Administrador informado não existe!"}), 400

        cursor.execute(
            "INSERT INTO materias (nome, descricao, carga_horaria, ementa, id_administrado) VALUES (?, ?, ?, ?, ?)",
            (nome, dados.get("descricao"), dados.get("carga_horaria"), dados.get("ementa"), id_administrado)
        )
        conexao.commit()
        return jsonify({"mensagem": "Matéria criada com sucesso!", "id": cursor.lastrowid}), 201
    finally:
        conexao.close()


# Atualizar matéria
@bp.route("/materias/<int:id_materia>", methods=["PUT"])
@roles_required("adm")
def atualizar_materia(id_materia):
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    id_administrado = dados.get("id_administrado")
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "materias", "id_materia", id_materia):
            return jsonify({"erro": "Matéria não encontrada!"}), 404
        if id_administrado is not None and not registro_existe(cursor, "adm", "id_administrado", id_administrado):
            return jsonify({"erro": "Administrador informado não existe!"}), 400

        cursor.execute(
            "UPDATE materias SET nome = ?, descricao = ?, carga_horaria = ?, ementa = ?, id_administrado = ? WHERE id_materia = ?",
            (nome, dados.get("descricao"), dados.get("carga_horaria"), dados.get("ementa"), id_administrado, id_materia)
        )
        conexao.commit()
        return jsonify({"mensagem": "Matéria atualizada com sucesso!"}), 200
    finally:
        conexao.close()


# Excluir matéria
@bp.route("/materias/<int:id_materia>", methods=["DELETE"])
@roles_required("adm")
def excluir_materia(id_materia):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "materias", "id_materia", id_materia):
            return jsonify({"erro": "Matéria não encontrada!"}), 404

        cursor.execute("DELETE FROM materias WHERE id_materia = ?", (id_materia,))
        conexao.commit()
        return jsonify({"mensagem": "Matéria excluída com sucesso!"}), 200
    finally:
        conexao.close()

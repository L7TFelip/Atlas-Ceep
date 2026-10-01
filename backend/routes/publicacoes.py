"""Publicações criadas pelo professor para uma turma/matéria."""

from datetime import date
from flask import Blueprint, jsonify, request

from ..auth_utils import roles_required, usuario_atual
from ..database.database import conectar_banco, registro_existe

bp = Blueprint("publicacoes", __name__)
TIPOS = {"atividade", "material", "aviso"}


def _listar_do_professor(cursor, id_professor):
    cursor.execute("""
        SELECT p.id_publicacao, p.titulo, p.descricao, p.tipo,
               p.data_publicacao, p.prazo_entrega,
               p.id_turma, t.nome AS turma,
               p.id_materia, m.nome AS materia,
               p.id_professor, pr.nome AS professor
        FROM publicacoes p
        JOIN turmas t ON t.id_turma = p.id_turma
        JOIN materias m ON m.id_materia = p.id_materia
        JOIN professor pr ON pr.id_professor = p.id_professor
        WHERE p.id_professor = ?
        ORDER BY p.data_publicacao DESC, p.id_publicacao DESC
    """, (id_professor,))
    return [dict(linha) for linha in cursor.fetchall()]


def _validar_publicacao(cursor, dados, id_professor):
    titulo = str(dados.get("titulo", "")).strip()
    tipo = dados.get("tipo")
    id_turma = dados.get("id_turma")
    id_materia = dados.get("id_materia")

    if not titulo:
        return "O título é obrigatório."
    if tipo not in TIPOS:
        return "Tipo de publicação inválido."
    if not id_turma or not registro_existe(cursor, "turmas", "id_turma", id_turma):
        return "Turma inválida."
    if not id_materia or not registro_existe(cursor, "materias", "id_materia", id_materia):
        return "Matéria inválida."

    cursor.execute(
        "SELECT 1 FROM professor_turma WHERE id_professor = ? AND id_turma = ?",
        (id_professor, id_turma),
    )
    if not cursor.fetchone():
        return "Essa turma não está associada ao professor."

    cursor.execute(
        "SELECT 1 FROM professor_materia WHERE id_professor = ? AND id_materia = ?",
        (id_professor, id_materia),
    )
    if not cursor.fetchone():
        return "Essa matéria não está associada ao professor."

    return None


@bp.get("/professor/opcoes")
@roles_required("professor")
def opcoes_professor():
    professor = usuario_atual()
    id_professor = professor["id_referencia"]
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT t.id_turma AS id, t.nome
            FROM professor_turma pt
            JOIN turmas t ON t.id_turma = pt.id_turma
            WHERE pt.id_professor = ?
            ORDER BY t.nome
        """, (id_professor,))
        turmas = [dict(l) for l in cursor.fetchall()]

        cursor.execute("""
            SELECT m.id_materia AS id, m.nome
            FROM professor_materia pm
            JOIN materias m ON m.id_materia = pm.id_materia
            WHERE pm.id_professor = ?
            ORDER BY m.nome
        """, (id_professor,))
        materias = [dict(l) for l in cursor.fetchall()]
        return jsonify({"turmas": turmas, "materias": materias})
    finally:
        conexao.close()


@bp.get("/professor/publicacoes")
@roles_required("professor")
def listar_publicacoes_professor():
    professor = usuario_atual()
    conexao = conectar_banco()
    try:
        return jsonify({"publicacoes": _listar_do_professor(conexao.cursor(), professor["id_referencia"])})
    finally:
        conexao.close()


@bp.post("/professor/publicacoes")
@roles_required("professor")
def criar_publicacao():
    professor = usuario_atual()
    id_professor = professor["id_referencia"]
    dados = request.get_json(silent=True) or {}

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        erro = _validar_publicacao(cursor, dados, id_professor)
        if erro:
            return jsonify({"erro": erro}), 400

        prazo = dados.get("prazo_entrega") if dados.get("tipo") == "atividade" else None
        cursor.execute("""
            INSERT INTO publicacoes
                (titulo, descricao, tipo, data_publicacao, prazo_entrega,
                 id_professor, id_turma, id_materia)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(dados.get("titulo")).strip(),
            str(dados.get("descricao", "")).strip() or None,
            dados.get("tipo"),
            dados.get("data_publicacao") or str(date.today()),
            prazo or None,
            id_professor,
            dados.get("id_turma"),
            dados.get("id_materia"),
        ))
        conexao.commit()
        return jsonify({"mensagem": "Publicação criada.", "id": cursor.lastrowid}), 201
    finally:
        conexao.close()


@bp.put("/professor/publicacoes/<int:id_publicacao>")
@roles_required("professor")
def atualizar_publicacao(id_publicacao):
    professor = usuario_atual()
    id_professor = professor["id_referencia"]
    dados = request.get_json(silent=True) or {}

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT 1 FROM publicacoes WHERE id_publicacao = ? AND id_professor = ?",
            (id_publicacao, id_professor),
        )
        if not cursor.fetchone():
            return jsonify({"erro": "Publicação não encontrada."}), 404

        erro = _validar_publicacao(cursor, dados, id_professor)
        if erro:
            return jsonify({"erro": erro}), 400

        prazo = dados.get("prazo_entrega") if dados.get("tipo") == "atividade" else None
        cursor.execute("""
            UPDATE publicacoes
            SET titulo = ?, descricao = ?, tipo = ?, data_publicacao = ?,
                prazo_entrega = ?, id_turma = ?, id_materia = ?
            WHERE id_publicacao = ? AND id_professor = ?
        """, (
            str(dados.get("titulo")).strip(),
            str(dados.get("descricao", "")).strip() or None,
            dados.get("tipo"),
            dados.get("data_publicacao") or str(date.today()),
            prazo or None,
            dados.get("id_turma"),
            dados.get("id_materia"),
            id_publicacao,
            id_professor,
        ))
        conexao.commit()
        return jsonify({"mensagem": "Publicação atualizada."})
    finally:
        conexao.close()


@bp.delete("/professor/publicacoes/<int:id_publicacao>")
@roles_required("professor")
def excluir_publicacao(id_publicacao):
    professor = usuario_atual()
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "DELETE FROM publicacoes WHERE id_publicacao = ? AND id_professor = ?",
            (id_publicacao, professor["id_referencia"]),
        )
        if cursor.rowcount == 0:
            return jsonify({"erro": "Publicação não encontrada."}), 404
        conexao.commit()
        return jsonify({"mensagem": "Publicação excluída."})
    finally:
        conexao.close()

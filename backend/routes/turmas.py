"""Rotas de turmas."""

from flask import Blueprint, jsonify, request

from ..database.database import conectar_banco, linha_para_dict, registro_existe
from ..auth_utils import roles_required

bp = Blueprint("turmas", __name__)


# ==================== TURMAS ====================

# Buscar todas as turmas
@bp.route("/turmas", methods=["GET"])
@roles_required("adm")
def listar_turmas():
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT t.*, GROUP_CONCAT(m.nome, ', ') AS materias
            FROM turmas t
            LEFT JOIN turma_materia tm ON tm.id_turma = t.id_turma
            LEFT JOIN materias m ON m.id_materia = tm.id_materia
            GROUP BY t.id_turma
            ORDER BY t.nome COLLATE NOCASE
        """)
        linhas = cursor.fetchall()
        return jsonify({"turmas": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Buscar turma específica
@bp.route("/turmas/<int:id_turma>", methods=["GET"])
@roles_required("adm")
def buscar_turma(id_turma):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM turmas WHERE id_turma = ?", (id_turma,))
        linha = cursor.fetchone()
        if not linha:
            return jsonify({"erro": "Turma não encontrada!"}), 404
        return jsonify(linha_para_dict(linha)), 200
    finally:
        conexao.close()


# Criar turma
@bp.route("/turmas", methods=["POST"])
@roles_required("adm")
def criar_turma():
    dados = request.get_json(silent=True) or {}
    nome = str(dados.get("nome", "")).strip()
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    materias = dados.get("materias", [])
    if not isinstance(materias, list):
        return jsonify({"erro": "O campo 'materias' deve ser uma lista de disciplinas."}), 400

    materias_validadas = []
    for materia in materias:
        if not isinstance(materia, dict):
            return jsonify({"erro": "Cada disciplina deve ser um objeto."}), 400
        nome_materia = str(materia.get("nome", "")).strip()
        if not nome_materia:
            return jsonify({"erro": "Toda disciplina precisa ter um nome."}), 400
        materias_validadas.append((nome_materia, materia.get("carga_horaria")))

    id_administrado = dados.get("id_administrado")
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if id_administrado is not None and not registro_existe(cursor, "adm", "id_administrado", id_administrado):
            return jsonify({"erro": "Administrador informado não existe!"}), 400

        cursor.execute(
            "INSERT INTO turmas (nome, sala, ano, semestre, id_administrado) VALUES (?, ?, ?, ?, ?)",
            (nome, dados.get("sala"), dados.get("ano"), dados.get("semestre"), id_administrado)
        )
        id_turma = cursor.lastrowid
        for nome_materia, carga_horaria in materias_validadas:
            cursor.execute(
                "INSERT INTO materias (nome, carga_horaria, id_administrado) VALUES (?, ?, ?)",
                (nome_materia, carga_horaria, id_administrado)
            )
            cursor.execute(
                "INSERT INTO turma_materia (id_turma, id_materia) VALUES (?, ?)",
                (id_turma, cursor.lastrowid)
            )
        conexao.commit()
        return jsonify({"mensagem": "Turma criada com sucesso!", "id": id_turma}), 201
    finally:
        conexao.close()


# Atualizar turma
@bp.route("/turmas/<int:id_turma>", methods=["PUT"])
@roles_required("adm")
def atualizar_turma(id_turma):
    dados = request.get_json(silent=True) or {}
    nome = str(dados.get("nome", "")).strip()
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    id_administrado = dados.get("id_administrado")
    materias = dados.get("materias") if "materias" in dados else None
    if materias is not None and not isinstance(materias, list):
        return jsonify({"erro": "O campo 'materias' deve ser uma lista de disciplinas."}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "turmas", "id_turma", id_turma):
            return jsonify({"erro": "Turma não encontrada!"}), 404
        if id_administrado is not None and not registro_existe(cursor, "adm", "id_administrado", id_administrado):
            return jsonify({"erro": "Administrador informado não existe!"}), 400

        materias_validadas = None
        if materias is not None:
            cursor.execute(
                "SELECT id_materia FROM turma_materia WHERE id_turma = ?",
                (id_turma,),
            )
            materias_da_turma = {linha["id_materia"] for linha in cursor.fetchall()}
            materias_validadas = []
            ids_materias_vistas = set()
            for materia in materias:
                if not isinstance(materia, dict):
                    return jsonify({"erro": "Cada disciplina deve ser um objeto."}), 400
                nome_materia = str(materia.get("nome", "")).strip()
                if not nome_materia:
                    return jsonify({"erro": "Toda disciplina precisa ter um nome."}), 400

                id_materia = materia.get("id_materia")
                if id_materia is not None:
                    try:
                        id_materia = int(id_materia)
                    except (TypeError, ValueError):
                        return jsonify({"erro": "Identificador de disciplina inválido."}), 400
                    if id_materia not in materias_da_turma or id_materia in ids_materias_vistas:
                        return jsonify({"erro": "A disciplina não pertence à turma ou foi repetida."}), 400
                    ids_materias_vistas.add(id_materia)
                materias_validadas.append((id_materia, nome_materia))

        cursor.execute(
            "UPDATE turmas SET nome = ?, sala = ?, ano = ?, semestre = ?, id_administrado = ? WHERE id_turma = ?",
            (nome, dados.get("sala"), dados.get("ano"), dados.get("semestre"), id_administrado, id_turma)
        )

        if materias_validadas is not None:
            vinculos = []
            for id_materia, nome_materia in materias_validadas:
                if id_materia is None:
                    cursor.execute(
                        "INSERT INTO materias (nome, id_administrado) VALUES (?, ?)",
                        (nome_materia, id_administrado),
                    )
                    id_materia = cursor.lastrowid
                else:
                    cursor.execute(
                        "UPDATE materias SET nome = ? WHERE id_materia = ?",
                        (nome_materia, id_materia),
                    )
                vinculos.append((id_turma, id_materia))

            cursor.execute("DELETE FROM turma_materia WHERE id_turma = ?", (id_turma,))
            cursor.executemany(
                "INSERT INTO turma_materia (id_turma, id_materia) VALUES (?, ?)",
                vinculos,
            )

        conexao.commit()
        return jsonify({"mensagem": "Turma atualizada com sucesso!"}), 200
    finally:
        conexao.close()


# Excluir turma
@bp.route("/turmas/<int:id_turma>", methods=["DELETE"])
@roles_required("adm")
def excluir_turma(id_turma):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "turmas", "id_turma", id_turma):
            return jsonify({"erro": "Turma não encontrada!"}), 404

        # Preserva os alunos cadastrados e remove apenas o vínculo com a turma.
        cursor.execute("UPDATE aluno SET id_turma = NULL WHERE id_turma = ?", (id_turma,))
        cursor.execute("DELETE FROM turmas WHERE id_turma = ?", (id_turma,))
        conexao.commit()
        return jsonify({"mensagem": "Turma excluída com sucesso!"}), 200
    finally:
        conexao.close()


# ==================== TURMA -> MATÉRIAS ====================

# Buscar matérias da turma
@bp.route("/turmas/<int:id_turma>/materias", methods=["GET"])
@roles_required("adm")
def listar_materias_da_turma(id_turma):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "turmas", "id_turma", id_turma):
            return jsonify({"erro": "Turma não encontrada!"}), 404

        cursor.execute("""
            SELECT materias.*
            FROM turma_materia
            JOIN materias ON materias.id_materia = turma_materia.id_materia
            WHERE turma_materia.id_turma = ?
        """, (id_turma,))
        linhas = cursor.fetchall()
        return jsonify({"materias": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Adicionar matéria à turma
@bp.route("/turmas/<int:id_turma>/materias", methods=["POST"])
@roles_required("adm")
def adicionar_materia_a_turma(id_turma):
    dados = request.get_json(silent=True) or {}
    id_materia = dados.get("id_materia")
    if not id_materia:
        return jsonify({"erro": "O campo 'id_materia' é obrigatório!"}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "turmas", "id_turma", id_turma):
            return jsonify({"erro": "Turma não encontrada!"}), 404
        if not registro_existe(cursor, "materias", "id_materia", id_materia):
            return jsonify({"erro": "Disciplina não encontrada!"}), 404

        cursor.execute(
            "SELECT 1 FROM turma_materia WHERE id_turma = ? AND id_materia = ?",
            (id_turma, id_materia)
        )
        if cursor.fetchone():
            return jsonify({"erro": "Essa disciplina já está associada à turma!"}), 409

        cursor.execute(
            "INSERT INTO turma_materia (id_turma, id_materia) VALUES (?, ?)",
            (id_turma, id_materia)
        )
        conexao.commit()
        return jsonify({"mensagem": "Disciplina adicionada à turma com sucesso!"}), 201
    finally:
        conexao.close()


# Remover matéria da turma
@bp.route("/turmas/<int:id_turma>/materias/<int:id_materia>", methods=["DELETE"])
@roles_required("adm")
def remover_materia_da_turma(id_turma, id_materia):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT 1 FROM turma_materia WHERE id_turma = ? AND id_materia = ?",
            (id_turma, id_materia)
        )
        if not cursor.fetchone():
            return jsonify({"erro": "Essa disciplina não está associada à turma!"}), 404

        cursor.execute(
            "DELETE FROM turma_materia WHERE id_turma = ? AND id_materia = ?",
            (id_turma, id_materia)
        )
        conexao.commit()
        return jsonify({"mensagem": "Disciplina removida da turma com sucesso!"}), 200
    finally:
        conexao.close()

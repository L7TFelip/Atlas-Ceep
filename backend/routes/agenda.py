"""Agenda do aluno: atividades do professor + anotações pessoais."""

from datetime import date
from flask import Blueprint, jsonify, request

from ..auth_utils import roles_required, usuario_atual
from ..database.database import conectar_banco

bp = Blueprint("agenda", __name__)
STATUS_VALIDOS = {"pending", "progress", "done"}


def _aluno_id():
    return usuario_atual()["id_referencia"]


def _tarefa_publicacao(linha):
    return {
        "id": f"pub:{linha['id_publicacao']}",
        "source": "professor",
        "sourceId": linha["id_publicacao"],
        "title": linha["titulo"],
        "subject": linha["materia"],
        "teacher": linha["professor"],
        "due": linha["prazo_entrega"] or linha["data_publicacao"],
        "created": linha["data_publicacao"],
        "description": linha["descricao"] or "",
        "status": linha["status"] or "pending",
        "submittedAt": linha["entregue_em"] or "",
        "inClass": True,
        "assignedOn": linha["data_publicacao"],
        "editable": False,
    }


def _tarefa_pessoal(linha):
    return {
        "id": f"pessoal:{linha['id_atividade']}",
        "source": "pessoal",
        "sourceId": linha["id_atividade"],
        "title": linha["titulo"],
        "subject": linha["disciplina"],
        "teacher": linha["professor_nome"] or "",
        "due": linha["prazo"],
        "created": linha["criada_em"],
        "description": linha["descricao"] or "",
        "status": linha["status"],
        "submittedAt": linha["entregue_em"] or "",
        "inClass": bool(linha["foi_passada_em_sala"]),
        "assignedOn": linha["data_passada"] or "",
        "editable": True,
    }


@bp.get("/aluno/agenda")
@roles_required("aluno")
def agenda_aluno():
    aluno = usuario_atual()
    id_aluno = aluno["id_referencia"]
    id_turma = aluno.get("id_turma")
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        tarefas = []
        avisos = []
        disciplinas = []

        if id_turma:
            cursor.execute("""
                SELECT m.id_materia, m.nome
                FROM turma_materia tm
                JOIN materias m ON m.id_materia = tm.id_materia
                WHERE tm.id_turma = ?
                ORDER BY m.nome COLLATE NOCASE
            """, (id_turma,))
            disciplinas = [dict(linha) for linha in cursor.fetchall()]

            cursor.execute("""
                SELECT p.id_publicacao, p.titulo, p.descricao, p.tipo,
                       p.data_publicacao, p.prazo_entrega,
                       m.nome AS materia, pr.nome AS professor,
                       ap.status, ap.entregue_em
                FROM publicacoes p
                JOIN materias m ON m.id_materia = p.id_materia
                JOIN professor pr ON pr.id_professor = p.id_professor
                LEFT JOIN aluno_publicacao ap
                    ON ap.id_publicacao = p.id_publicacao AND ap.id_aluno = ?
                WHERE p.id_turma = ?
                ORDER BY p.data_publicacao DESC, p.id_publicacao DESC
            """, (id_aluno, id_turma))
            for linha in cursor.fetchall():
                if linha["tipo"] == "atividade":
                    tarefas.append(_tarefa_publicacao(linha))
                elif linha["tipo"] in {"aviso", "material"}:
                    prefixo = "Material: " if linha["tipo"] == "material" else ""
                    avisos.append({
                        "id": f"pub:{linha['id_publicacao']}",
                        "source": "professor",
                        "sourceId": linha["id_publicacao"],
                        "title": prefixo + linha["titulo"],
                        "date": linha["data_publicacao"],
                        "editable": False,
                    })

        cursor.execute(
            "SELECT * FROM atividades_pessoais WHERE id_aluno = ? ORDER BY prazo, id_atividade",
            (id_aluno,),
        )
        tarefas.extend(_tarefa_pessoal(l) for l in cursor.fetchall())

        cursor.execute(
            "SELECT * FROM avisos_aluno WHERE id_aluno = ? ORDER BY data_aviso DESC, id_aviso DESC",
            (id_aluno,),
        )
        avisos.extend({
            "id": f"pessoal:{l['id_aviso']}",
            "source": "pessoal",
            "sourceId": l["id_aviso"],
            "title": l["titulo"],
            "date": l["data_aviso"],
            "editable": True,
        } for l in cursor.fetchall())

        cursor.execute("""
            SELECT id_evento, nome, descricao, horario, local,
                   data_evento, tipo, publico
            FROM eventos
            WHERE publico IN ('todos', 'alunos')
            ORDER BY COALESCE(data_evento, '9999-12-31'), horario
        """)
        eventos = [dict(l) for l in cursor.fetchall()]

        return jsonify({
            "usuario": aluno,
            "subjects": disciplinas,
            "tasks": tarefas,
            "notices": avisos,
            "events": eventos,
        })
    finally:
        conexao.close()


@bp.post("/aluno/atividades")
@roles_required("aluno")
def criar_atividade_pessoal():
    dados = request.get_json(silent=True) or {}
    titulo = str(dados.get("titulo", "")).strip()
    disciplina = str(dados.get("disciplina", "")).strip()
    prazo = str(dados.get("prazo", "")).strip()
    if not titulo or not disciplina or not prazo:
        return jsonify({"erro": "Título, disciplina e prazo são obrigatórios."}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            INSERT INTO atividades_pessoais
                (id_aluno, titulo, disciplina, professor_nome, prazo, descricao,
                 foi_passada_em_sala, data_passada, status, entregue_em, criada_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, ?)
        """, (
            _aluno_id(), titulo, disciplina,
            str(dados.get("professor", "")).strip() or None,
            prazo,
            str(dados.get("descricao", "")).strip() or None,
            1 if dados.get("foi_passada_em_sala", True) else 0,
            dados.get("data_passada") or None,
            str(date.today()),
        ))
        conexao.commit()
        return jsonify({"mensagem": "Atividade criada.", "id": cursor.lastrowid}), 201
    finally:
        conexao.close()


@bp.put("/aluno/atividades/<int:id_atividade>")
@roles_required("aluno")
def atualizar_atividade_pessoal(id_atividade):
    dados = request.get_json(silent=True) or {}
    titulo = str(dados.get("titulo", "")).strip()
    disciplina = str(dados.get("disciplina", "")).strip()
    prazo = str(dados.get("prazo", "")).strip()
    if not titulo or not disciplina or not prazo:
        return jsonify({"erro": "Título, disciplina e prazo são obrigatórios."}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            UPDATE atividades_pessoais
            SET titulo = ?, disciplina = ?, professor_nome = ?, prazo = ?,
                descricao = ?, foi_passada_em_sala = ?, data_passada = ?
            WHERE id_atividade = ? AND id_aluno = ?
        """, (
            titulo, disciplina,
            str(dados.get("professor", "")).strip() or None,
            prazo,
            str(dados.get("descricao", "")).strip() or None,
            1 if dados.get("foi_passada_em_sala", True) else 0,
            dados.get("data_passada") or None,
            id_atividade, _aluno_id(),
        ))
        if cursor.rowcount == 0:
            return jsonify({"erro": "Atividade não encontrada."}), 404
        conexao.commit()
        return jsonify({"mensagem": "Atividade atualizada."})
    finally:
        conexao.close()


@bp.delete("/aluno/atividades/<int:id_atividade>")
@roles_required("aluno")
def excluir_atividade_pessoal(id_atividade):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "DELETE FROM atividades_pessoais WHERE id_atividade = ? AND id_aluno = ?",
            (id_atividade, _aluno_id()),
        )
        if cursor.rowcount == 0:
            return jsonify({"erro": "Atividade não encontrada."}), 404
        conexao.commit()
        return jsonify({"mensagem": "Atividade excluída."})
    finally:
        conexao.close()


@bp.patch("/aluno/tarefas/<string:origem>/<int:id_tarefa>/status")
@roles_required("aluno")
def atualizar_status(origem, id_tarefa):
    dados = request.get_json(silent=True) or {}
    status = dados.get("status")
    entregue_em = dados.get("entregue_em")
    if status not in STATUS_VALIDOS:
        return jsonify({"erro": "Status inválido."}), 400

    id_aluno = _aluno_id()
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if origem == "pessoal":
            cursor.execute("""
                UPDATE atividades_pessoais
                SET status = ?, entregue_em = ?
                WHERE id_atividade = ? AND id_aluno = ?
            """, (status, entregue_em or None, id_tarefa, id_aluno))
            if cursor.rowcount == 0:
                return jsonify({"erro": "Atividade não encontrada."}), 404
        elif origem == "professor":
            aluno = usuario_atual()
            cursor.execute(
                "SELECT 1 FROM publicacoes WHERE id_publicacao = ? AND id_turma = ? AND tipo = 'atividade'",
                (id_tarefa, aluno.get("id_turma")),
            )
            if not cursor.fetchone():
                return jsonify({"erro": "Publicação não encontrada para a turma do aluno."}), 404
            cursor.execute("""
                INSERT INTO aluno_publicacao (id_aluno, id_publicacao, status, entregue_em)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id_aluno, id_publicacao)
                DO UPDATE SET status = excluded.status, entregue_em = excluded.entregue_em
            """, (id_aluno, id_tarefa, status, entregue_em or None))
        else:
            return jsonify({"erro": "Origem inválida."}), 400

        conexao.commit()
        return jsonify({"mensagem": "Status atualizado."})
    finally:
        conexao.close()


@bp.post("/aluno/avisos")
@roles_required("aluno")
def criar_aviso_pessoal():
    dados = request.get_json(silent=True) or {}
    titulo = str(dados.get("titulo", "")).strip()
    if not titulo:
        return jsonify({"erro": "A mensagem do aviso é obrigatória."}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO avisos_aluno (id_aluno, titulo, data_aviso) VALUES (?, ?, ?)",
            (_aluno_id(), titulo, dados.get("data") or str(date.today())),
        )
        conexao.commit()
        return jsonify({"mensagem": "Aviso criado.", "id": cursor.lastrowid}), 201
    finally:
        conexao.close()


@bp.delete("/aluno/avisos/<int:id_aviso>")
@roles_required("aluno")
def excluir_aviso_pessoal(id_aviso):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "DELETE FROM avisos_aluno WHERE id_aviso = ? AND id_aluno = ?",
            (id_aviso, _aluno_id()),
        )
        if cursor.rowcount == 0:
            return jsonify({"erro": "Aviso não encontrado."}), 404
        conexao.commit()
        return jsonify({"mensagem": "Aviso excluído."})
    finally:
        conexao.close()

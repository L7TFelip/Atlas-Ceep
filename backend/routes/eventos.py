"""Rotas de eventos institucionais."""

from flask import Blueprint, jsonify, request

from ..auth_utils import login_required, roles_required, usuario_atual
from ..database.database import conectar_banco, linha_para_dict

bp = Blueprint("eventos", __name__)
TIPOS = {"evento", "reuniao", "comemoracao", "aviso"}
PUBLICOS = {"todos", "alunos", "professores"}


@bp.get("/eventos")
@login_required
def listar_eventos():
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT e.*, a.nome AS administrador
            FROM eventos e
            LEFT JOIN adm a ON a.id_administrado = e.id_administrado
            ORDER BY COALESCE(e.data_evento, '9999-12-31'), e.horario, e.id_evento
        """)
        return jsonify({"eventos": [linha_para_dict(l) for l in cursor.fetchall()]})
    finally:
        conexao.close()


@bp.get("/eventos/<int:id_evento>")
@login_required
def buscar_evento(id_evento):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM eventos WHERE id_evento = ?", (id_evento,))
        linha = cursor.fetchone()
        if not linha:
            return jsonify({"erro": "Evento não encontrado."}), 404
        return jsonify(linha_para_dict(linha))
    finally:
        conexao.close()


def _validar(dados):
    nome = str(dados.get("nome", "")).strip()
    tipo = dados.get("tipo", "evento")
    publico = dados.get("publico", "todos")
    data_evento = dados.get("data_evento")
    if not nome:
        return "O título do evento é obrigatório."
    if tipo not in TIPOS:
        return "Tipo de evento inválido."
    if publico not in PUBLICOS:
        return "Público inválido."
    if not data_evento:
        return "A data do evento é obrigatória."
    return None


@bp.post("/eventos")
@roles_required("adm")
def criar_evento():
    dados = request.get_json(silent=True) or {}
    erro = _validar(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    admin = usuario_atual()
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            INSERT INTO eventos
                (nome, descricao, horario, local, id_administrado, data_evento, tipo, publico)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(dados.get("nome")).strip(),
            str(dados.get("descricao", "")).strip() or None,
            dados.get("horario") or None,
            str(dados.get("local", "")).strip() or None,
            admin["id_referencia"],
            dados.get("data_evento"),
            dados.get("tipo", "evento"),
            dados.get("publico", "todos"),
        ))
        conexao.commit()
        return jsonify({"mensagem": "Evento criado.", "id": cursor.lastrowid}), 201
    finally:
        conexao.close()


@bp.put("/eventos/<int:id_evento>")
@roles_required("adm")
def atualizar_evento(id_evento):
    dados = request.get_json(silent=True) or {}
    erro = _validar(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    admin = usuario_atual()
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            UPDATE eventos
            SET nome = ?, descricao = ?, horario = ?, local = ?,
                data_evento = ?, tipo = ?, publico = ?, id_administrado = ?
            WHERE id_evento = ?
        """, (
            str(dados.get("nome")).strip(),
            str(dados.get("descricao", "")).strip() or None,
            dados.get("horario") or None,
            str(dados.get("local", "")).strip() or None,
            dados.get("data_evento"),
            dados.get("tipo", "evento"),
            dados.get("publico", "todos"),
            admin["id_referencia"],
            id_evento,
        ))
        if cursor.rowcount == 0:
            return jsonify({"erro": "Evento não encontrado."}), 404
        conexao.commit()
        return jsonify({"mensagem": "Evento atualizado."})
    finally:
        conexao.close()


@bp.delete("/eventos/<int:id_evento>")
@roles_required("adm")
def excluir_evento(id_evento):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM eventos WHERE id_evento = ?", (id_evento,))
        if cursor.rowcount == 0:
            return jsonify({"erro": "Evento não encontrado."}), 404
        conexao.commit()
        return jsonify({"mensagem": "Evento excluído."})
    finally:
        conexao.close()

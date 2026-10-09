"""Publicações criadas pelo professor para uma turma/matéria."""

from datetime import date
from io import BytesIO
from pathlib import PurePath
from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from ..auth_utils import roles_required, usuario_atual
from ..database.database import conectar_banco, registro_existe

bp = Blueprint("publicacoes", __name__)
TIPOS = {"atividade", "material", "aviso"}
MAX_IMAGENS_PUBLICACAO = 5
MAX_BYTES_IMAGEM = 5 * 1024 * 1024


def _dados_requisicao():
    if request.mimetype == "multipart/form-data":
        return request.form
    return request.get_json(silent=True) or {}


def _detectar_imagem(dados):
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if dados.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if dados.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(dados) >= 12 and dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return "image/webp"
    return None


def _preparar_imagens(arquivos):
    selecionados = [arquivo for arquivo in arquivos if arquivo and arquivo.filename]
    if len(selecionados) > MAX_IMAGENS_PUBLICACAO:
        return None, f"Anexe no máximo {MAX_IMAGENS_PUBLICACAO} imagens por envio."

    imagens = []
    for arquivo in selecionados:
        dados = arquivo.stream.read(MAX_BYTES_IMAGEM + 1)
        if not dados:
            return None, "Uma das imagens está vazia."
        if len(dados) > MAX_BYTES_IMAGEM:
            return None, "Cada imagem pode ter no máximo 5 MB."
        mime_type = _detectar_imagem(dados)
        if not mime_type:
            return None, "Formato não suportado. Use PNG, JPEG, GIF ou WebP."
        nome_original = secure_filename(PurePath(arquivo.filename).name) or "imagem"
        imagens.append({"dados": dados, "mime_type": mime_type, "nome_original": nome_original})
    return imagens, None


def _salvar_imagens(cursor, id_publicacao, imagens):
    if not imagens:
        return
    cursor.execute(
        "SELECT COALESCE(MAX(ordem), -1) + 1 FROM publicacao_imagens WHERE id_publicacao = ?",
        (id_publicacao,),
    )
    primeira_ordem = cursor.fetchone()[0]
    cursor.executemany("""
        INSERT INTO publicacao_imagens
            (id_publicacao, nome_original, mime_type, dados, ordem)
        VALUES (?, ?, ?, ?, ?)
    """, [
        (id_publicacao, imagem["nome_original"], imagem["mime_type"], imagem["dados"], primeira_ordem + ordem)
        for ordem, imagem in enumerate(imagens)
    ])


def imagens_por_publicacao(cursor, publicacoes):
    ids = [item["id_publicacao"] for item in publicacoes]
    resultado = {id_publicacao: [] for id_publicacao in ids}
    if not ids:
        return resultado

    placeholders = ",".join("?" for _ in ids)
    cursor.execute(f"""
        SELECT id_imagem, id_publicacao, nome_original, mime_type
        FROM publicacao_imagens
        WHERE id_publicacao IN ({placeholders})
        ORDER BY ordem, id_imagem
    """, ids)
    for linha in cursor.fetchall():
        resultado[linha["id_publicacao"]].append({
            "id": linha["id_imagem"],
            "nome": linha["nome_original"],
            "mime_type": linha["mime_type"],
            "url": f"/api/publicacoes/{linha['id_publicacao']}/imagens/{linha['id_imagem']}",
        })
    return resultado


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
    publicacoes = [dict(linha) for linha in cursor.fetchall()]
    imagens = imagens_por_publicacao(cursor, publicacoes)
    for publicacao in publicacoes:
        publicacao["imagens"] = imagens[publicacao["id_publicacao"]]
    return publicacoes


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
        return "Disciplina inválida."

    cursor.execute(
        "SELECT 1 FROM professor_turma WHERE id_professor = ? AND id_turma = ?",
        (id_professor, id_turma),
    )
    if not cursor.fetchone():
        return "Essa turma não está associada ao professor."

    cursor.execute(
        "SELECT 1 FROM turma_materia WHERE id_turma = ? AND id_materia = ?",
        (id_turma, id_materia),
    )
    if not cursor.fetchone():
        return "Essa disciplina não está associada à turma selecionada."

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
            SELECT DISTINCT t.id_turma, m.id_materia AS id, m.nome
            FROM professor_turma pt
            JOIN turma_materia tm ON tm.id_turma = pt.id_turma
            JOIN turmas t ON t.id_turma = tm.id_turma
            JOIN materias m ON m.id_materia = tm.id_materia
            WHERE pt.id_professor = ?
            ORDER BY t.nome, m.nome
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
    dados = _dados_requisicao()
    imagens, erro_imagens = _preparar_imagens(request.files.getlist("imagens"))
    if erro_imagens:
        return jsonify({"erro": erro_imagens}), 400

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
        id_publicacao = cursor.lastrowid
        _salvar_imagens(cursor, id_publicacao, imagens)
        conexao.commit()
        return jsonify({"mensagem": "Publicação criada.", "id": id_publicacao, "imagens": len(imagens)}), 201
    finally:
        conexao.close()


@bp.put("/professor/publicacoes/<int:id_publicacao>")
@roles_required("professor")
def atualizar_publicacao(id_publicacao):
    professor = usuario_atual()
    id_professor = professor["id_referencia"]
    dados = _dados_requisicao()
    imagens, erro_imagens = _preparar_imagens(request.files.getlist("imagens"))
    if erro_imagens:
        return jsonify({"erro": erro_imagens}), 400

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
        _salvar_imagens(cursor, id_publicacao, imagens)
        conexao.commit()
        return jsonify({"mensagem": "Publicação atualizada.", "imagens": len(imagens)})
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


@bp.get("/publicacoes/<int:id_publicacao>/imagens/<int:id_imagem>")
@roles_required("professor", "aluno")
def servir_imagem_publicacao(id_publicacao, id_imagem):
    usuario = usuario_atual()
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT i.nome_original, i.mime_type, i.dados,
                   p.id_professor, p.id_turma
            FROM publicacao_imagens i
            JOIN publicacoes p ON p.id_publicacao = i.id_publicacao
            WHERE p.id_publicacao = ? AND i.id_imagem = ?
        """, (id_publicacao, id_imagem))
        imagem = cursor.fetchone()
        if not imagem:
            return jsonify({"erro": "Imagem não encontrada."}), 404

        if usuario["papel"] == "professor" and imagem["id_professor"] != usuario["id_referencia"]:
            return jsonify({"erro": "Imagem não encontrada."}), 404
        if usuario["papel"] == "aluno" and imagem["id_turma"] != usuario.get("id_turma"):
            return jsonify({"erro": "Imagem não encontrada."}), 404

        resposta = send_file(
            BytesIO(imagem["dados"]),
            mimetype=imagem["mime_type"],
            download_name=imagem["nome_original"],
            as_attachment=False,
        )
        resposta.headers["Cache-Control"] = "private, max-age=3600"
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        return resposta
    finally:
        conexao.close()

"""Rotas de professores."""

from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

from ..database.database import conectar_banco, linha_para_dict, registro_existe
from ..auth_utils import roles_required

bp = Blueprint("professores", __name__)


def _validar_ids_turmas(cursor, ids_turmas):
    if not isinstance(ids_turmas, list):
        return None, "O campo 'ids_turmas' deve ser uma lista."

    ids_validos = []
    for id_turma in ids_turmas:
        try:
            id_turma = int(id_turma)
        except (TypeError, ValueError):
            return None, "A lista de turmas contém um identificador inválido."
        if id_turma <= 0 or id_turma in ids_validos:
            return None, "A lista de turmas contém um identificador inválido ou repetido."
        if not registro_existe(cursor, "turmas", "id_turma", id_turma):
            return None, "Uma das turmas informadas não existe."
        ids_validos.append(id_turma)
    return ids_validos, None


# ==================== PROFESSORES ====================

# Buscar todos os professores
@bp.route("/professores", methods=["GET"])
@roles_required("adm")
def listar_professores():
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT p.*, u.login AS email,
                   GROUP_CONCAT(DISTINCT t.nome) AS turmas,
                   GROUP_CONCAT(DISTINCT t.id_turma) AS ids_turmas
            FROM professor p
            LEFT JOIN usuarios u
                ON u.papel = 'professor' AND u.id_referencia = p.id_professor
            LEFT JOIN professor_turma pt ON pt.id_professor = p.id_professor
            LEFT JOIN turmas t ON t.id_turma = pt.id_turma
            GROUP BY p.id_professor
            ORDER BY p.nome COLLATE NOCASE
        """)
        linhas = cursor.fetchall()
        return jsonify({"professores": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Buscar professor específico
@bp.route("/professores/<int:id_professor>", methods=["GET"])
@roles_required("adm")
def buscar_professor(id_professor):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT * FROM professor WHERE id_professor = ?",
            (id_professor,)
        )

        linha = cursor.fetchone()

        if not linha:
            return jsonify({"erro": "Professor não encontrado!"}), 404

        return jsonify(linha_para_dict(linha)), 200

    finally:
        conexao.close()


# Criar professor
@bp.route("/professores", methods=["POST"])
@roles_required("adm")
def criar_professor():
    dados = request.get_json(silent=True) or {}

    nome = dados.get("nome")

    if not nome:
        return jsonify({
            "erro": "O campo 'nome' é obrigatório!"
        }), 400

    email = str(dados.get("email", "")).strip().lower()
    senha = str(dados.get("senha", ""))

    if not email:
        return jsonify({
            "erro": "O campo 'email' é obrigatório!"
        }), 400

    if not senha:
        return jsonify({
            "erro": "O campo 'senha' é obrigatório!"
        }), 400

    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        ids_turmas, erro_turmas = _validar_ids_turmas(cursor, dados.get("ids_turmas", []))
        if erro_turmas:
            return jsonify({"erro": erro_turmas}), 400

        # O e-mail também é o identificador usado no login.
        cursor.execute(
            "SELECT 1 FROM usuarios WHERE lower(login) = ?",
            (email,)
        )

        if cursor.fetchone():
            return jsonify({
                "erro": "Esse e-mail já está cadastrado!"
            }), 409

        # Cria o professor
        cursor.execute(
            """
            INSERT INTO professor
                (nome, data_contratacao, telefone)
            VALUES (?, ?, ?)
            """,
            (
                nome,
                dados.get("data_contratacao"),
                dados.get("telefone")
            )
        )

        id_professor = cursor.lastrowid

        # Cria o usuário vinculado ao professor
        senha_hash = generate_password_hash(senha)

        cursor.execute(
            """
            INSERT INTO usuarios
                (login, senha_hash, papel, id_referencia)
            VALUES (?, ?, 'professor', ?)
            """,
            (
                email,
                senha_hash,
                id_professor
            )
        )

        cursor.executemany(
            "INSERT INTO professor_turma (id_professor, id_turma) VALUES (?, ?)",
            [(id_professor, id_turma) for id_turma in ids_turmas],
        )

        id_usuario = cursor.lastrowid

        conexao.commit()

        return jsonify({
            "mensagem": "Professor e usuário criados com sucesso!",
            "professor": {
                "id": id_professor,
                "nome": nome
            },
            "usuario": {
                "id": id_usuario,
                "email": email,
                "ids_turmas": ids_turmas
            }
        }), 201

    except Exception as erro:
        conexao.rollback()

        return jsonify({
            "erro": "Erro ao criar professor.",
            "detalhes": str(erro)
        }), 500

    finally:
        conexao.close()


# Atualizar professor
@bp.route("/professores/<int:id_professor>", methods=["PUT"])
@roles_required("adm")
def atualizar_professor(id_professor):
    dados = request.get_json(silent=True) or {}

    nome = dados.get("nome")

    if not nome:
        return jsonify({
            "erro": "O campo 'nome' é obrigatório!"
        }), 400

    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        ids_turmas = None
        if "ids_turmas" in dados:
            ids_turmas, erro_turmas = _validar_ids_turmas(cursor, dados["ids_turmas"])
            if erro_turmas:
                return jsonify({"erro": erro_turmas}), 400

        if not registro_existe(
            cursor,
            "professor",
            "id_professor",
            id_professor
        ):
            return jsonify({
                "erro": "Professor não encontrado!"
            }), 404

        if "senha" in dados and not str(dados.get("senha", "")):
            return jsonify({"erro": "A nova senha não pode ser vazia."}), 400

        if "email" in dados:
            email = str(dados.get("email", "")).strip().lower()
            if not email:
                return jsonify({"erro": "O campo 'email' não pode ser vazio."}), 400
            cursor.execute(
                "SELECT id_usuario FROM usuarios WHERE papel = 'professor' AND id_referencia = ?",
                (id_professor,),
            )
            usuario = cursor.fetchone()
            if usuario:
                cursor.execute(
                    "SELECT 1 FROM usuarios WHERE lower(login) = ? AND id_usuario != ?",
                    (email, usuario["id_usuario"]),
                )
                if cursor.fetchone():
                    return jsonify({"erro": "Esse e-mail já está cadastrado."}), 409
                cursor.execute(
                    "UPDATE usuarios SET login = ? WHERE id_usuario = ?",
                    (email, usuario["id_usuario"]),
                )

        cursor.execute(
            """
            UPDATE professor
            SET
                nome = ?,
                data_contratacao = ?,
                telefone = ?
            WHERE id_professor = ?
            """,
            (
                nome,
                dados.get("data_contratacao"),
                dados.get("telefone"),
                id_professor
            )
        )

        if ids_turmas is not None:
            cursor.execute("DELETE FROM professor_turma WHERE id_professor = ?", (id_professor,))
            cursor.executemany(
                "INSERT INTO professor_turma (id_professor, id_turma) VALUES (?, ?)",
                [(id_professor, id_turma) for id_turma in ids_turmas],
            )

        if "senha" in dados:
            cursor.execute(
                "UPDATE usuarios SET senha_hash = ? WHERE papel = 'professor' AND id_referencia = ?",
                (generate_password_hash(str(dados["senha"])), id_professor),
            )
            if cursor.rowcount == 0:
                return jsonify({"erro": "A conta de acesso do professor não foi encontrada."}), 404

        conexao.commit()

        return jsonify({
            "mensagem": "Professor atualizado com sucesso!"
        }), 200

    finally:
        conexao.close()


# Excluir professor
@bp.route("/professores/<int:id_professor>", methods=["DELETE"])
@roles_required("adm")
def excluir_professor(id_professor):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        if not registro_existe(
            cursor,
            "professor",
            "id_professor",
            id_professor
        ):
            return jsonify({
                "erro": "Professor não encontrado!"
            }), 404

        # Remove o usuário vinculado ao professor
        cursor.execute(
            """
            DELETE FROM usuarios
            WHERE papel = 'professor'
            AND id_referencia = ?
            """,
            (id_professor,)
        )

        # Remove o professor
        cursor.execute(
            "DELETE FROM professor WHERE id_professor = ?",
            (id_professor,)
        )

        conexao.commit()

        return jsonify({
            "mensagem": "Professor excluído com sucesso!"
        }), 200

    finally:
        conexao.close()


# ==================== PROFESSOR -> TURMAS ====================

# Buscar turmas do professor
@bp.route("/professores/<int:id_professor>/turmas", methods=["GET"])
@roles_required("adm")
def listar_turmas_do_professor(id_professor):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        if not registro_existe(
            cursor,
            "professor",
            "id_professor",
            id_professor
        ):
            return jsonify({
                "erro": "Professor não encontrado!"
            }), 404

        cursor.execute(
            """
            SELECT turmas.*
            FROM professor_turma
            JOIN turmas
                ON turmas.id_turma = professor_turma.id_turma
            WHERE professor_turma.id_professor = ?
            """,
            (id_professor,)
        )

        linhas = cursor.fetchall()

        return jsonify({
            "turmas": [linha_para_dict(l) for l in linhas]
        }), 200

    finally:
        conexao.close()


# Adicionar turma ao professor
@bp.route("/professores/<int:id_professor>/turmas", methods=["POST"])
@roles_required("adm")
def adicionar_turma_ao_professor(id_professor):
    dados = request.get_json(silent=True) or {}

    id_turma = dados.get("id_turma")

    if not id_turma:
        return jsonify({
            "erro": "O campo 'id_turma' é obrigatório!"
        }), 400

    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        if not registro_existe(
            cursor,
            "professor",
            "id_professor",
            id_professor
        ):
            return jsonify({
                "erro": "Professor não encontrado!"
            }), 404

        if not registro_existe(
            cursor,
            "turmas",
            "id_turma",
            id_turma
        ):
            return jsonify({
                "erro": "Turma não encontrada!"
            }), 404

        cursor.execute(
            """
            SELECT 1
            FROM professor_turma
            WHERE id_professor = ?
            AND id_turma = ?
            """,
            (id_professor, id_turma)
        )

        if cursor.fetchone():
            return jsonify({
                "erro": "Essa turma já está associada ao professor!"
            }), 409

        cursor.execute(
            """
            INSERT INTO professor_turma
                (id_professor, id_turma)
            VALUES (?, ?)
            """,
            (id_professor, id_turma)
        )

        conexao.commit()

        return jsonify({
            "mensagem": "Turma adicionada ao professor com sucesso!"
        }), 201

    finally:
        conexao.close()


# Remover turma do professor
@bp.route(
    "/professores/<int:id_professor>/turmas/<int:id_turma>",
    methods=["DELETE"]
)
@roles_required("adm")
def remover_turma_do_professor(id_professor, id_turma):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM professor_turma
            WHERE id_professor = ?
            AND id_turma = ?
            """,
            (id_professor, id_turma)
        )

        if not cursor.fetchone():
            return jsonify({
                "erro": "Essa turma não está associada ao professor!"
            }), 404

        cursor.execute(
            """
            DELETE FROM professor_turma
            WHERE id_professor = ?
            AND id_turma = ?
            """,
            (id_professor, id_turma)
        )

        conexao.commit()

        return jsonify({
            "mensagem": "Turma removida do professor com sucesso!"
        }), 200

    finally:
        conexao.close()


# ==================== PROFESSOR -> MATÉRIAS ====================

# Buscar matérias do professor
@bp.route("/professores/<int:id_professor>/materias", methods=["GET"])
@roles_required("adm")
def listar_materias_do_professor(id_professor):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        if not registro_existe(
            cursor,
            "professor",
            "id_professor",
            id_professor
        ):
            return jsonify({
                "erro": "Professor não encontrado!"
            }), 404

        cursor.execute(
            """
            SELECT materias.*
            FROM professor_materia
            JOIN materias
                ON materias.id_materia = professor_materia.id_materia
            WHERE professor_materia.id_professor = ?
            """,
            (id_professor,)
        )

        linhas = cursor.fetchall()

        return jsonify({
            "materias": [linha_para_dict(l) for l in linhas]
        }), 200

    finally:
        conexao.close()


# Adicionar matéria ao professor
@bp.route("/professores/<int:id_professor>/materias", methods=["POST"])
@roles_required("adm")
def adicionar_materia_ao_professor(id_professor):
    dados = request.get_json(silent=True) or {}

    id_materia = dados.get("id_materia")

    if not id_materia:
        return jsonify({
            "erro": "O campo 'id_materia' é obrigatório!"
        }), 400

    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        if not registro_existe(
            cursor,
            "professor",
            "id_professor",
            id_professor
        ):
            return jsonify({
                "erro": "Professor não encontrado!"
            }), 404

        if not registro_existe(
            cursor,
            "materias",
            "id_materia",
            id_materia
        ):
            return jsonify({
                "erro": "Disciplina não encontrada!"
            }), 404

        cursor.execute(
            """
            SELECT 1
            FROM professor_materia
            WHERE id_professor = ?
            AND id_materia = ?
            """,
            (id_professor, id_materia)
        )

        if cursor.fetchone():
            return jsonify({
                "erro": "Essa disciplina já está associada ao professor!"
            }), 409

        cursor.execute(
            """
            INSERT INTO professor_materia
                (id_professor, id_materia)
            VALUES (?, ?)
            """,
            (id_professor, id_materia)
        )

        conexao.commit()

        return jsonify({
            "mensagem": "Disciplina adicionada ao professor com sucesso!"
        }), 201

    finally:
        conexao.close()


# Remover matéria ao professor
@bp.route(
    "/professores/<int:id_professor>/materias/<int:id_materia>",
    methods=["DELETE"]
)
@roles_required("adm")
def remover_materia_do_professor(id_professor, id_materia):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM professor_materia
            WHERE id_professor = ?
            AND id_materia = ?
            """,
            (id_professor, id_materia)
        )

        if not cursor.fetchone():
            return jsonify({
                "erro": "Essa disciplina não está associada ao professor!"
            }), 404

        cursor.execute(
            """
            DELETE FROM professor_materia
            WHERE id_professor = ?
            AND id_materia = ?
            """,
            (id_professor, id_materia)
        )

        conexao.commit()

        return jsonify({
            "mensagem": "Disciplina removida do professor com sucesso!"
        }), 200

    finally:
        conexao.close()


# ==================== PROFESSOR -> EVENTOS ====================

# Buscar eventos do professor
@bp.route("/professores/<int:id_professor>/eventos", methods=["GET"])
@roles_required("adm")
def listar_eventos_do_professor(id_professor):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        if not registro_existe(
            cursor,
            "professor",
            "id_professor",
            id_professor
        ):
            return jsonify({
                "erro": "Professor não encontrado!"
            }), 404

        cursor.execute(
            """
            SELECT eventos.*
            FROM professor_evento
            JOIN eventos
                ON eventos.id_evento = professor_evento.id_evento
            WHERE professor_evento.id_professor = ?
            """,
            (id_professor,)
        )

        linhas = cursor.fetchall()

        return jsonify({
            "eventos": [linha_para_dict(l) for l in linhas]
        }), 200

    finally:
        conexao.close()


# Adicionar evento ao professor
@bp.route("/professores/<int:id_professor>/eventos", methods=["POST"])
@roles_required("adm")
def adicionar_evento_ao_professor(id_professor):
    dados = request.get_json(silent=True) or {}

    id_evento = dados.get("id_evento")

    if not id_evento:
        return jsonify({
            "erro": "O campo 'id_evento' é obrigatório!"
        }), 400

    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        if not registro_existe(
            cursor,
            "professor",
            "id_professor",
            id_professor
        ):
            return jsonify({
                "erro": "Professor não encontrado!"
            }), 404

        if not registro_existe(
            cursor,
            "eventos",
            "id_evento",
            id_evento
        ):
            return jsonify({
                "erro": "Evento não encontrado!"
            }), 404

        cursor.execute(
            """
            SELECT 1
            FROM professor_evento
            WHERE id_professor = ?
            AND id_evento = ?
            """,
            (id_professor, id_evento)
        )

        if cursor.fetchone():
            return jsonify({
                "erro": "Esse evento já está associado ao professor!"
            }), 409

        cursor.execute(
            """
            INSERT INTO professor_evento
                (id_professor, id_evento)
            VALUES (?, ?)
            """,
            (id_professor, id_evento)
        )

        conexao.commit()

        return jsonify({
            "mensagem": "Evento adicionado ao professor com sucesso!"
        }), 201

    finally:
        conexao.close()


# Remover evento ao professor
@bp.route(
    "/professores/<int:id_professor>/eventos/<int:id_evento>",
    methods=["DELETE"]
)
@roles_required("adm")
def remover_evento_do_professor(id_professor, id_evento):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM professor_evento
            WHERE id_professor = ?
            AND id_evento = ?
            """,
            (id_professor, id_evento)
        )

        if not cursor.fetchone():
            return jsonify({
                "erro": "Esse evento não está associado ao professor!"
            }), 404

        cursor.execute(
            """
            DELETE FROM professor_evento
            WHERE id_professor = ?
            AND id_evento = ?
            """,
            (id_professor, id_evento)
        )

        conexao.commit()

        return jsonify({
            "mensagem": "Evento removido do professor com sucesso!"
        }), 200

    finally:
        conexao.close()

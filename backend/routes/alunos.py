from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

from ..database.database import conectar_banco, registro_existe
from ..auth_utils import roles_required

bp = Blueprint("alunos", __name__)


@bp.route("/alunos", methods=["POST"])
@roles_required("adm")
def criar_aluno():
    dados = request.get_json(silent=True) or {}

    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    id_turma = dados.get("id_turma")

    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        # Verifica se a turma existe
        if id_turma is not None:
            if not registro_existe(cursor, "turmas", "id_turma", id_turma):
                return jsonify({"erro": "Turma informada não existe!"}), 400

        # ---------------------------------------------------------
        # Cria o aluno
        # ---------------------------------------------------------
        cursor.execute(
            """
            INSERT INTO aluno
                (nome, email, telefone, data_nascimento, id_turma)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                nome,
                dados.get("email"),
                dados.get("telefone"),
                dados.get("data_nascimento"),
                id_turma,
            ),
        )

        id_aluno = cursor.lastrowid

        # ---------------------------------------------------------
        # Cria o usuário do aluno
        # ---------------------------------------------------------

        # Se o CGM não for informado, gera um automaticamente.
        cgm = str(dados.get("cgm", "")).strip()

        if not cgm:
            cgm = f"{1000000000 + id_aluno}"

        # Senha inicial
        senha = str(dados.get("senha", "atlas123"))

        if not senha:
            return jsonify({"erro": "A senha não pode ser vazia!"}), 400

        # Verifica se o CGM/login já existe
        cursor.execute(
            "SELECT 1 FROM usuarios WHERE login = ?",
            (cgm,),
        )

        if cursor.fetchone():
            conexao.rollback()
            return jsonify({
                "erro": "O CGM informado já está cadastrado!"
            }), 409

        senha_hash = generate_password_hash(senha)

        cursor.execute(
            """
            INSERT INTO usuarios
                (login, senha_hash, papel, id_referencia)
            VALUES (?, ?, 'aluno', ?)
            """,
            (
                cgm,
                senha_hash,
                id_aluno,
            ),
        )

        id_usuario = cursor.lastrowid

        # Só confirma os dois registros juntos
        conexao.commit()

        return jsonify({
            "mensagem": "Aluno e usuário criados com sucesso!",
            "aluno": {
                "id": id_aluno,
                "nome": nome,
                "email": dados.get("email"),
                "telefone": dados.get("telefone"),
                "data_nascimento": dados.get("data_nascimento"),
                "id_turma": id_turma,
            },
            "usuario": {
                "id": id_usuario,
                "cgm": cgm,
                "senha": senha,
            }
        }), 201

    except Exception as erro:
        conexao.rollback()
        return jsonify({
            "erro": "Erro ao criar aluno.",
            "detalhes": str(erro),
        }), 500

    finally:
        conexao.close()
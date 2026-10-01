from functools import wraps
from flask import jsonify, session

from .database.database import conectar_banco


def usuario_atual():
    id_usuario = session.get("id_usuario")
    if not id_usuario:
        return None

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id_usuario, login, papel, id_referencia FROM usuarios WHERE id_usuario = ?",
            (id_usuario,),
        )
        usuario = cursor.fetchone()
        if not usuario:
            session.clear()
            return None

        dados = dict(usuario)
        papel = dados["papel"]
        ref = dados["id_referencia"]

        if papel == "aluno":
            cursor.execute("""
                SELECT a.id_aluno AS id, a.nome, a.email, a.id_turma,
                       t.nome AS turma
                FROM aluno a
                LEFT JOIN turmas t ON t.id_turma = a.id_turma
                WHERE a.id_aluno = ?
            """, (ref,))
        elif papel == "professor":
            cursor.execute(
                "SELECT id_professor AS id, nome, telefone, atributo FROM professor WHERE id_professor = ?",
                (ref,),
            )
        else:
            cursor.execute(
                "SELECT id_administrado AS id, nome, telefone, nivel_acesso FROM adm WHERE id_administrado = ?",
                (ref,),
            )

        perfil = cursor.fetchone()
        if not perfil:
            session.clear()
            return None

        dados.update(dict(perfil))
        return dados
    finally:
        conexao.close()


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        usuario = usuario_atual()
        if not usuario:
            return jsonify({"erro": "Faça login para continuar."}), 401
        return func(*args, **kwargs)

    return wrapper


def roles_required(*papeis):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            usuario = usuario_atual()
            if not usuario:
                return jsonify({"erro": "Faça login para continuar."}), 401
            if usuario["papel"] not in papeis:
                return jsonify({"erro": "Você não tem permissão para esta operação."}), 403
            return func(*args, **kwargs)

        return wrapper

    return decorator

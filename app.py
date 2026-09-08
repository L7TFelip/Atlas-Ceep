from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)


def conectar_banco():
    conexao = sqlite3.connect("atlas.db")
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_banco():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Administradores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adm (
            id_administrado INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(150) NOT NULL,
            telefone VARCHAR(20),
            nivel_acesso VARCHAR(50)
        )
    """)

    # Turmas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turmas (
            id_turma INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(100) NOT NULL,
            sala VARCHAR(20),
            ano INTEGER,
            semestre INTEGER,
            id_administrado INTEGER,
            FOREIGN KEY (id_administrado)
                REFERENCES adm(id_administrado)
        )
    """)

    # Alunos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aluno (
            id_aluno INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(150) NOT NULL,
            email VARCHAR(150),
            telefone VARCHAR(20),
            data_nascimento VARCHAR(10),
            id_turma INTEGER,
            FOREIGN KEY (id_turma)
                REFERENCES turmas(id_turma)
        )
    """)

    # Professores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor (
            id_professor INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(150) NOT NULL,
            data_contratacao VARCHAR(10),
            telefone VARCHAR(20),
            atributo VARCHAR(100)
        )
    """)

    # Matérias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materias (
            id_materia INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(150) NOT NULL,
            descricao VARCHAR(500),
            carga_horaria INTEGER,
            ementa VARCHAR(2000),
            id_administrado INTEGER,
            FOREIGN KEY (id_administrado)
                REFERENCES adm(id_administrado)
        )
    """)

    # Eventos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id_evento INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(150) NOT NULL,
            descricao VARCHAR(500),
            horario VARCHAR(20),
            local VARCHAR(200),
            id_administrado INTEGER,
            FOREIGN KEY (id_administrado)
                REFERENCES adm(id_administrado)
        )
    """)

    # Aluno - Matéria
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aluno_materia (
            id_aluno INTEGER,
            id_materia INTEGER,
            PRIMARY KEY (id_aluno, id_materia),
            FOREIGN KEY (id_aluno)
                REFERENCES aluno(id_aluno),
            FOREIGN KEY (id_materia)
                REFERENCES materias(id_materia)
        )
    """)

    # Professor - Turma
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_turma (
            id_professor INTEGER,
            id_turma INTEGER,
            PRIMARY KEY (id_professor, id_turma),
            FOREIGN KEY (id_professor)
                REFERENCES professor(id_professor),
            FOREIGN KEY (id_turma)
                REFERENCES turmas(id_turma)
        )
    """)

    # Professor - Matéria
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_materia (
            id_professor INTEGER,
            id_materia INTEGER,
            PRIMARY KEY (id_professor, id_materia),
            FOREIGN KEY (id_professor)
                REFERENCES professor(id_professor),
            FOREIGN KEY (id_materia)
                REFERENCES materias(id_materia)
        )
    """)

    # Turma - Matéria
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turma_materia (
            id_turma INTEGER,
            id_materia INTEGER,
            PRIMARY KEY (id_turma, id_materia),
            FOREIGN KEY (id_turma)
                REFERENCES turmas(id_turma),
            FOREIGN KEY (id_materia)
                REFERENCES materias(id_materia)
        )
    """)

    # Professor - Evento
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_evento (
            id_professor INTEGER,
            id_evento INTEGER,
            PRIMARY KEY (id_professor, id_evento),
            FOREIGN KEY (id_professor)
                REFERENCES professor(id_professor),
            FOREIGN KEY (id_evento)
                REFERENCES eventos(id_evento)
        )
    """)

    conexao.commit()
    conexao.close()


# Converte uma linha do SQLite em dicionário
def linha_para_dict(linha):
    return dict(linha) if linha else None


# Verifica se um registro existe em uma tabela pelo id
def registro_existe(cursor, tabela, coluna_id, valor_id):
    cursor.execute(f"SELECT 1 FROM {tabela} WHERE {coluna_id} = ?", (valor_id,))
    return cursor.fetchone() is not None


@app.route("/")
def inicio():
    return jsonify({
        "mensagem": "API funcionando!",
        "banco": "atlas.db"
    })


# ==================== ADMINISTRADORES ====================

# Buscar todos os administradores
@app.route("/adms", methods=["GET"])
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
@app.route("/adms/<int:id_administrado>", methods=["GET"])
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
@app.route("/adms", methods=["POST"])
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
@app.route("/adms/<int:id_administrado>", methods=["PUT"])
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
@app.route("/adms/<int:id_administrado>", methods=["DELETE"])
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


# ==================== TURMAS ====================

# Buscar todas as turmas
@app.route("/turmas", methods=["GET"])
def listar_turmas():
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM turmas")
        linhas = cursor.fetchall()
        return jsonify({"turmas": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Buscar turma específica
@app.route("/turmas/<int:id_turma>", methods=["GET"])
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
@app.route("/turmas", methods=["POST"])
def criar_turma():
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
            "INSERT INTO turmas (nome, sala, ano, semestre, id_administrado) VALUES (?, ?, ?, ?, ?)",
            (nome, dados.get("sala"), dados.get("ano"), dados.get("semestre"), id_administrado)
        )
        conexao.commit()
        return jsonify({"mensagem": "Turma criada com sucesso!", "id": cursor.lastrowid}), 201
    finally:
        conexao.close()


# Atualizar turma
@app.route("/turmas/<int:id_turma>", methods=["PUT"])
def atualizar_turma(id_turma):
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    id_administrado = dados.get("id_administrado")
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "turmas", "id_turma", id_turma):
            return jsonify({"erro": "Turma não encontrada!"}), 404
        if id_administrado is not None and not registro_existe(cursor, "adm", "id_administrado", id_administrado):
            return jsonify({"erro": "Administrador informado não existe!"}), 400

        cursor.execute(
            "UPDATE turmas SET nome = ?, sala = ?, ano = ?, semestre = ?, id_administrado = ? WHERE id_turma = ?",
            (nome, dados.get("sala"), dados.get("ano"), dados.get("semestre"), id_administrado, id_turma)
        )
        conexao.commit()
        return jsonify({"mensagem": "Turma atualizada com sucesso!"}), 200
    finally:
        conexao.close()


# Excluir turma
@app.route("/turmas/<int:id_turma>", methods=["DELETE"])
def excluir_turma(id_turma):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "turmas", "id_turma", id_turma):
            return jsonify({"erro": "Turma não encontrada!"}), 404

        cursor.execute("DELETE FROM turmas WHERE id_turma = ?", (id_turma,))
        conexao.commit()
        return jsonify({"mensagem": "Turma excluída com sucesso!"}), 200
    finally:
        conexao.close()


# ==================== ALUNOS ====================

# Buscar todos os alunos
@app.route("/alunos", methods=["GET"])
def listar_alunos():
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM aluno")
        linhas = cursor.fetchall()
        return jsonify({"alunos": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Buscar aluno específico
@app.route("/alunos/<int:id_aluno>", methods=["GET"])
def buscar_aluno(id_aluno):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM aluno WHERE id_aluno = ?", (id_aluno,))
        linha = cursor.fetchone()
        if not linha:
            return jsonify({"erro": "Aluno não encontrado!"}), 404
        return jsonify(linha_para_dict(linha)), 200
    finally:
        conexao.close()


# Criar aluno
@app.route("/alunos", methods=["POST"])
def criar_aluno():
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    id_turma = dados.get("id_turma")
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if id_turma is not None and not registro_existe(cursor, "turmas", "id_turma", id_turma):
            return jsonify({"erro": "Turma informada não existe!"}), 400

        cursor.execute(
            "INSERT INTO aluno (nome, email, telefone, data_nascimento, id_turma) VALUES (?, ?, ?, ?, ?)",
            (nome, dados.get("email"), dados.get("telefone"), dados.get("data_nascimento"), id_turma)
        )
        conexao.commit()
        return jsonify({"mensagem": "Aluno criado com sucesso!", "id": cursor.lastrowid}), 201
    finally:
        conexao.close()


# Atualizar aluno
@app.route("/alunos/<int:id_aluno>", methods=["PUT"])
def atualizar_aluno(id_aluno):
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    id_turma = dados.get("id_turma")
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "aluno", "id_aluno", id_aluno):
            return jsonify({"erro": "Aluno não encontrado!"}), 404
        if id_turma is not None and not registro_existe(cursor, "turmas", "id_turma", id_turma):
            return jsonify({"erro": "Turma informada não existe!"}), 400

        cursor.execute(
            "UPDATE aluno SET nome = ?, email = ?, telefone = ?, data_nascimento = ?, id_turma = ? WHERE id_aluno = ?",
            (nome, dados.get("email"), dados.get("telefone"), dados.get("data_nascimento"), id_turma, id_aluno)
        )
        conexao.commit()
        return jsonify({"mensagem": "Aluno atualizado com sucesso!"}), 200
    finally:
        conexao.close()


# Excluir aluno
@app.route("/alunos/<int:id_aluno>", methods=["DELETE"])
def excluir_aluno(id_aluno):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "aluno", "id_aluno", id_aluno):
            return jsonify({"erro": "Aluno não encontrado!"}), 404

        cursor.execute("DELETE FROM aluno WHERE id_aluno = ?", (id_aluno,))
        conexao.commit()
        return jsonify({"mensagem": "Aluno excluído com sucesso!"}), 200
    finally:
        conexao.close()


# ==================== PROFESSORES ====================

# Buscar todos os professores
@app.route("/professores", methods=["GET"])
def listar_professores():
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM professor")
        linhas = cursor.fetchall()
        return jsonify({"professores": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Buscar professor específico
@app.route("/professores/<int:id_professor>", methods=["GET"])
def buscar_professor(id_professor):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM professor WHERE id_professor = ?", (id_professor,))
        linha = cursor.fetchone()
        if not linha:
            return jsonify({"erro": "Professor não encontrado!"}), 404
        return jsonify(linha_para_dict(linha)), 200
    finally:
        conexao.close()


# Criar professor
@app.route("/professores", methods=["POST"])
def criar_professor():
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO professor (nome, data_contratacao, telefone, atributo) VALUES (?, ?, ?, ?)",
            (nome, dados.get("data_contratacao"), dados.get("telefone"), dados.get("atributo"))
        )
        conexao.commit()
        return jsonify({"mensagem": "Professor criado com sucesso!", "id": cursor.lastrowid}), 201
    finally:
        conexao.close()


# Atualizar professor
@app.route("/professores/<int:id_professor>", methods=["PUT"])
def atualizar_professor(id_professor):
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "professor", "id_professor", id_professor):
            return jsonify({"erro": "Professor não encontrado!"}), 404

        cursor.execute(
            "UPDATE professor SET nome = ?, data_contratacao = ?, telefone = ?, atributo = ? WHERE id_professor = ?",
            (nome, dados.get("data_contratacao"), dados.get("telefone"), dados.get("atributo"), id_professor)
        )
        conexao.commit()
        return jsonify({"mensagem": "Professor atualizado com sucesso!"}), 200
    finally:
        conexao.close()


# Excluir professor
@app.route("/professores/<int:id_professor>", methods=["DELETE"])
def excluir_professor(id_professor):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "professor", "id_professor", id_professor):
            return jsonify({"erro": "Professor não encontrado!"}), 404

        cursor.execute("DELETE FROM professor WHERE id_professor = ?", (id_professor,))
        conexao.commit()
        return jsonify({"mensagem": "Professor excluído com sucesso!"}), 200
    finally:
        conexao.close()


# ==================== MATÉRIAS ====================

# Buscar todas as matérias
@app.route("/materias", methods=["GET"])
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
@app.route("/materias/<int:id_materia>", methods=["GET"])
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
@app.route("/materias", methods=["POST"])
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
@app.route("/materias/<int:id_materia>", methods=["PUT"])
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
@app.route("/materias/<int:id_materia>", methods=["DELETE"])
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


# ==================== EVENTOS ====================

# Buscar todos os eventos
@app.route("/eventos", methods=["GET"])
def listar_eventos():
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM eventos")
        linhas = cursor.fetchall()
        return jsonify({"eventos": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Buscar evento específico
@app.route("/eventos/<int:id_evento>", methods=["GET"])
def buscar_evento(id_evento):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM eventos WHERE id_evento = ?", (id_evento,))
        linha = cursor.fetchone()
        if not linha:
            return jsonify({"erro": "Evento não encontrado!"}), 404
        return jsonify(linha_para_dict(linha)), 200
    finally:
        conexao.close()


# Criar evento
@app.route("/eventos", methods=["POST"])
def criar_evento():
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
            "INSERT INTO eventos (nome, descricao, horario, local, id_administrado) VALUES (?, ?, ?, ?, ?)",
            (nome, dados.get("descricao"), dados.get("horario"), dados.get("local"), id_administrado)
        )
        conexao.commit()
        return jsonify({"mensagem": "Evento criado com sucesso!", "id": cursor.lastrowid}), 201
    finally:
        conexao.close()


# Atualizar evento
@app.route("/eventos/<int:id_evento>", methods=["PUT"])
def atualizar_evento(id_evento):
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório!"}), 400

    id_administrado = dados.get("id_administrado")
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "eventos", "id_evento", id_evento):
            return jsonify({"erro": "Evento não encontrado!"}), 404
        if id_administrado is not None and not registro_existe(cursor, "adm", "id_administrado", id_administrado):
            return jsonify({"erro": "Administrador informado não existe!"}), 400

        cursor.execute(
            "UPDATE eventos SET nome = ?, descricao = ?, horario = ?, local = ?, id_administrado = ? WHERE id_evento = ?",
            (nome, dados.get("descricao"), dados.get("horario"), dados.get("local"), id_administrado, id_evento)
        )
        conexao.commit()
        return jsonify({"mensagem": "Evento atualizado com sucesso!"}), 200
    finally:
        conexao.close()


# Excluir evento
@app.route("/eventos/<int:id_evento>", methods=["DELETE"])
def excluir_evento(id_evento):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "eventos", "id_evento", id_evento):
            return jsonify({"erro": "Evento não encontrado!"}), 404

        cursor.execute("DELETE FROM eventos WHERE id_evento = ?", (id_evento,))
        conexao.commit()
        return jsonify({"mensagem": "Evento excluído com sucesso!"}), 200
    finally:
        conexao.close()


# ==================== ALUNO -> MATÉRIAS ====================

# Buscar matérias do aluno
@app.route("/alunos/<int:id_aluno>/materias", methods=["GET"])
def listar_materias_do_aluno(id_aluno):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "aluno", "id_aluno", id_aluno):
            return jsonify({"erro": "Aluno não encontrado!"}), 404

        cursor.execute("""
            SELECT materias.*
            FROM aluno_materia
            JOIN materias ON materias.id_materia = aluno_materia.id_materia
            WHERE aluno_materia.id_aluno = ?
        """, (id_aluno,))
        linhas = cursor.fetchall()
        return jsonify({"materias": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Adicionar matéria ao aluno
@app.route("/alunos/<int:id_aluno>/materias", methods=["POST"])
def adicionar_materia_ao_aluno(id_aluno):
    dados = request.get_json(silent=True) or {}
    id_materia = dados.get("id_materia")
    if not id_materia:
        return jsonify({"erro": "O campo 'id_materia' é obrigatório!"}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "aluno", "id_aluno", id_aluno):
            return jsonify({"erro": "Aluno não encontrado!"}), 404
        if not registro_existe(cursor, "materias", "id_materia", id_materia):
            return jsonify({"erro": "Matéria não encontrada!"}), 404

        cursor.execute(
            "SELECT 1 FROM aluno_materia WHERE id_aluno = ? AND id_materia = ?",
            (id_aluno, id_materia)
        )
        if cursor.fetchone():
            return jsonify({"erro": "Essa matéria já está associada ao aluno!"}), 409

        cursor.execute(
            "INSERT INTO aluno_materia (id_aluno, id_materia) VALUES (?, ?)",
            (id_aluno, id_materia)
        )
        conexao.commit()
        return jsonify({"mensagem": "Matéria adicionada ao aluno com sucesso!"}), 201
    finally:
        conexao.close()


# Remover matéria do aluno
@app.route("/alunos/<int:id_aluno>/materias/<int:id_materia>", methods=["DELETE"])
def remover_materia_do_aluno(id_aluno, id_materia):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT 1 FROM aluno_materia WHERE id_aluno = ? AND id_materia = ?",
            (id_aluno, id_materia)
        )
        if not cursor.fetchone():
            return jsonify({"erro": "Essa matéria não está associada ao aluno!"}), 404

        cursor.execute(
            "DELETE FROM aluno_materia WHERE id_aluno = ? AND id_materia = ?",
            (id_aluno, id_materia)
        )
        conexao.commit()
        return jsonify({"mensagem": "Matéria removida do aluno com sucesso!"}), 200
    finally:
        conexao.close()


# ==================== PROFESSOR -> TURMAS ====================

# Buscar turmas do professor
@app.route("/professores/<int:id_professor>/turmas", methods=["GET"])
def listar_turmas_do_professor(id_professor):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "professor", "id_professor", id_professor):
            return jsonify({"erro": "Professor não encontrado!"}), 404

        cursor.execute("""
            SELECT turmas.*
            FROM professor_turma
            JOIN turmas ON turmas.id_turma = professor_turma.id_turma
            WHERE professor_turma.id_professor = ?
        """, (id_professor,))
        linhas = cursor.fetchall()
        return jsonify({"turmas": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Adicionar turma ao professor
@app.route("/professores/<int:id_professor>/turmas", methods=["POST"])
def adicionar_turma_ao_professor(id_professor):
    dados = request.get_json(silent=True) or {}
    id_turma = dados.get("id_turma")
    if not id_turma:
        return jsonify({"erro": "O campo 'id_turma' é obrigatório!"}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "professor", "id_professor", id_professor):
            return jsonify({"erro": "Professor não encontrado!"}), 404
        if not registro_existe(cursor, "turmas", "id_turma", id_turma):
            return jsonify({"erro": "Turma não encontrada!"}), 404

        cursor.execute(
            "SELECT 1 FROM professor_turma WHERE id_professor = ? AND id_turma = ?",
            (id_professor, id_turma)
        )
        if cursor.fetchone():
            return jsonify({"erro": "Essa turma já está associada ao professor!"}), 409

        cursor.execute(
            "INSERT INTO professor_turma (id_professor, id_turma) VALUES (?, ?)",
            (id_professor, id_turma)
        )
        conexao.commit()
        return jsonify({"mensagem": "Turma adicionada ao professor com sucesso!"}), 201
    finally:
        conexao.close()


# Remover turma do professor
@app.route("/professores/<int:id_professor>/turmas/<int:id_turma>", methods=["DELETE"])
def remover_turma_do_professor(id_professor, id_turma):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT 1 FROM professor_turma WHERE id_professor = ? AND id_turma = ?",
            (id_professor, id_turma)
        )
        if not cursor.fetchone():
            return jsonify({"erro": "Essa turma não está associada ao professor!"}), 404

        cursor.execute(
            "DELETE FROM professor_turma WHERE id_professor = ? AND id_turma = ?",
            (id_professor, id_turma)
        )
        conexao.commit()
        return jsonify({"mensagem": "Turma removida do professor com sucesso!"}), 200
    finally:
        conexao.close()


# ==================== PROFESSOR -> MATÉRIAS ====================

# Buscar matérias do professor
@app.route("/professores/<int:id_professor>/materias", methods=["GET"])
def listar_materias_do_professor(id_professor):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "professor", "id_professor", id_professor):
            return jsonify({"erro": "Professor não encontrado!"}), 404

        cursor.execute("""
            SELECT materias.*
            FROM professor_materia
            JOIN materias ON materias.id_materia = professor_materia.id_materia
            WHERE professor_materia.id_professor = ?
        """, (id_professor,))
        linhas = cursor.fetchall()
        return jsonify({"materias": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Adicionar matéria ao professor
@app.route("/professores/<int:id_professor>/materias", methods=["POST"])
def adicionar_materia_ao_professor(id_professor):
    dados = request.get_json(silent=True) or {}
    id_materia = dados.get("id_materia")
    if not id_materia:
        return jsonify({"erro": "O campo 'id_materia' é obrigatório!"}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "professor", "id_professor", id_professor):
            return jsonify({"erro": "Professor não encontrado!"}), 404
        if not registro_existe(cursor, "materias", "id_materia", id_materia):
            return jsonify({"erro": "Matéria não encontrada!"}), 404

        cursor.execute(
            "SELECT 1 FROM professor_materia WHERE id_professor = ? AND id_materia = ?",
            (id_professor, id_materia)
        )
        if cursor.fetchone():
            return jsonify({"erro": "Essa matéria já está associada ao professor!"}), 409

        cursor.execute(
            "INSERT INTO professor_materia (id_professor, id_materia) VALUES (?, ?)",
            (id_professor, id_materia)
        )
        conexao.commit()
        return jsonify({"mensagem": "Matéria adicionada ao professor com sucesso!"}), 201
    finally:
        conexao.close()


# Remover matéria do professor
@app.route("/professores/<int:id_professor>/materias/<int:id_materia>", methods=["DELETE"])
def remover_materia_do_professor(id_professor, id_materia):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT 1 FROM professor_materia WHERE id_professor = ? AND id_materia = ?",
            (id_professor, id_materia)
        )
        if not cursor.fetchone():
            return jsonify({"erro": "Essa matéria não está associada ao professor!"}), 404

        cursor.execute(
            "DELETE FROM professor_materia WHERE id_professor = ? AND id_materia = ?",
            (id_professor, id_materia)
        )
        conexao.commit()
        return jsonify({"mensagem": "Matéria removida do professor com sucesso!"}), 200
    finally:
        conexao.close()


# ==================== TURMA -> MATÉRIAS ====================

# Buscar matérias da turma
@app.route("/turmas/<int:id_turma>/materias", methods=["GET"])
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
@app.route("/turmas/<int:id_turma>/materias", methods=["POST"])
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
            return jsonify({"erro": "Matéria não encontrada!"}), 404

        cursor.execute(
            "SELECT 1 FROM turma_materia WHERE id_turma = ? AND id_materia = ?",
            (id_turma, id_materia)
        )
        if cursor.fetchone():
            return jsonify({"erro": "Essa matéria já está associada à turma!"}), 409

        cursor.execute(
            "INSERT INTO turma_materia (id_turma, id_materia) VALUES (?, ?)",
            (id_turma, id_materia)
        )
        conexao.commit()
        return jsonify({"mensagem": "Matéria adicionada à turma com sucesso!"}), 201
    finally:
        conexao.close()


# Remover matéria da turma
@app.route("/turmas/<int:id_turma>/materias/<int:id_materia>", methods=["DELETE"])
def remover_materia_da_turma(id_turma, id_materia):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT 1 FROM turma_materia WHERE id_turma = ? AND id_materia = ?",
            (id_turma, id_materia)
        )
        if not cursor.fetchone():
            return jsonify({"erro": "Essa matéria não está associada à turma!"}), 404

        cursor.execute(
            "DELETE FROM turma_materia WHERE id_turma = ? AND id_materia = ?",
            (id_turma, id_materia)
        )
        conexao.commit()
        return jsonify({"mensagem": "Matéria removida da turma com sucesso!"}), 200
    finally:
        conexao.close()


# ==================== PROFESSOR -> EVENTOS ====================

# Buscar eventos do professor
@app.route("/professores/<int:id_professor>/eventos", methods=["GET"])
def listar_eventos_do_professor(id_professor):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "professor", "id_professor", id_professor):
            return jsonify({"erro": "Professor não encontrado!"}), 404

        cursor.execute("""
            SELECT eventos.*
            FROM professor_evento
            JOIN eventos ON eventos.id_evento = professor_evento.id_evento
            WHERE professor_evento.id_professor = ?
        """, (id_professor,))
        linhas = cursor.fetchall()
        return jsonify({"eventos": [linha_para_dict(l) for l in linhas]}), 200
    finally:
        conexao.close()


# Adicionar evento ao professor
@app.route("/professores/<int:id_professor>/eventos", methods=["POST"])
def adicionar_evento_ao_professor(id_professor):
    dados = request.get_json(silent=True) or {}
    id_evento = dados.get("id_evento")
    if not id_evento:
        return jsonify({"erro": "O campo 'id_evento' é obrigatório!"}), 400

    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        if not registro_existe(cursor, "professor", "id_professor", id_professor):
            return jsonify({"erro": "Professor não encontrado!"}), 404
        if not registro_existe(cursor, "eventos", "id_evento", id_evento):
            return jsonify({"erro": "Evento não encontrado!"}), 404

        cursor.execute(
            "SELECT 1 FROM professor_evento WHERE id_professor = ? AND id_evento = ?",
            (id_professor, id_evento)
        )
        if cursor.fetchone():
            return jsonify({"erro": "Esse evento já está associado ao professor!"}), 409

        cursor.execute(
            "INSERT INTO professor_evento (id_professor, id_evento) VALUES (?, ?)",
            (id_professor, id_evento)
        )
        conexao.commit()
        return jsonify({"mensagem": "Evento adicionado ao professor com sucesso!"}), 201
    finally:
        conexao.close()


# Remover evento do professor
@app.route("/professores/<int:id_professor>/eventos/<int:id_evento>", methods=["DELETE"])
def remover_evento_do_professor(id_professor, id_evento):
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT 1 FROM professor_evento WHERE id_professor = ? AND id_evento = ?",
            (id_professor, id_evento)
        )
        if not cursor.fetchone():
            return jsonify({"erro": "Esse evento não está associado ao professor!"}), 404

        cursor.execute(
            "DELETE FROM professor_evento WHERE id_professor = ? AND id_evento = ?",
            (id_professor, id_evento)
        )
        conexao.commit()
        return jsonify({"mensagem": "Evento removido do professor com sucesso!"}), 200
    finally:
        conexao.close()



if __name__ == "__main__":
    criar_banco()
    app.run(debug=True)

from flask import Flask, jsonify
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


@app.route("/")
def inicio():
    return jsonify({
        "mensagem": "API funcionando!",
        "banco": "atlas.db"
    })


if __name__ == "__main__":
    criar_banco()
    app.run(debug=True)
    ##teste
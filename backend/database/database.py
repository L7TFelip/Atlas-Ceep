"""Banco SQLite do Atlas CEEP.

Mantém as tabelas originais do projeto e acrescenta as estruturas necessárias
para autenticação, publicações do professor e agenda persistente do aluno.
"""

import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent / "atlas.db"
ADMIN_BOOTSTRAP_EMAIL = "admin@atlas.com"
ADMIN_BOOTSTRAP_PASSWORD = "atlas123"


def conectar_banco():
    conexao = sqlite3.connect(DB_PATH)
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.row_factory = sqlite3.Row
    return conexao


def linha_para_dict(linha):
    return dict(linha) if linha else None


def registro_existe(cursor, tabela, coluna_id, valor_id):
    cursor.execute(f"SELECT 1 FROM {tabela} WHERE {coluna_id} = ?", (valor_id,))
    return cursor.fetchone() is not None


def _colunas(cursor, tabela):
    cursor.execute(f"PRAGMA table_info({tabela})")
    return {linha[1] for linha in cursor.fetchall()}


def _garantir_coluna(cursor, tabela, coluna, definicao):
    if coluna not in _colunas(cursor, tabela):
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")


def _seed_dados(cursor):
    """Garante o administrador inicial e sua conta de acesso."""
    cursor.execute("SELECT COUNT(*) FROM adm")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO adm (nome, telefone, nivel_acesso) VALUES (?, ?, ?)",
            ("Administrador", None, "total"),
        )

    cursor.execute("SELECT id_administrado FROM adm ORDER BY id_administrado LIMIT 1")
    id_administrador = cursor.fetchone()[0]
    cursor.execute(
        "SELECT 1 FROM usuarios WHERE papel = 'adm' AND id_referencia = ?",
        (id_administrador,),
    )
    if cursor.fetchone():
        return

    cursor.execute("SELECT 1 FROM usuarios WHERE lower(login) = ?", (ADMIN_BOOTSTRAP_EMAIL,))
    if cursor.fetchone():
        raise ValueError(
            f"O login inicial {ADMIN_BOOTSTRAP_EMAIL!r} já está associado a outra conta."
        )

    cursor.execute(
        """INSERT INTO usuarios (login, senha_hash, papel, id_referencia)
           VALUES (?, ?, 'adm', ?)""",
        (
            ADMIN_BOOTSTRAP_EMAIL,
            generate_password_hash(ADMIN_BOOTSTRAP_PASSWORD),
            id_administrador,
        ),
    )


def criar_banco():
    # Cria toda a estrutura do banco, sem popular tabelas com dados de exemplo.
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Tabelas originais -------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adm (
            id_administrado INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(150) NOT NULL,
            telefone VARCHAR(20),
            nivel_acesso VARCHAR(50)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turmas (
            id_turma INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(100) NOT NULL,
            sala VARCHAR(20),
            ano INTEGER,
            semestre INTEGER,
            id_administrado INTEGER,
            FOREIGN KEY (id_administrado) REFERENCES adm(id_administrado)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aluno (
            id_aluno INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(150) NOT NULL,
            email VARCHAR(150),
            telefone VARCHAR(20),
            data_nascimento VARCHAR(10),
            id_turma INTEGER,
            FOREIGN KEY (id_turma) REFERENCES turmas(id_turma)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor (
            id_professor INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(150) NOT NULL,
            data_contratacao VARCHAR(10),
            telefone VARCHAR(20),
            atributo VARCHAR(100)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materias (
            id_materia INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(150) NOT NULL,
            descricao VARCHAR(500),
            carga_horaria INTEGER,
            ementa VARCHAR(2000),
            id_administrado INTEGER,
            FOREIGN KEY (id_administrado) REFERENCES adm(id_administrado)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id_evento INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(150) NOT NULL,
            descricao VARCHAR(700),
            horario VARCHAR(20),
            local VARCHAR(200),
            id_administrado INTEGER,
            data_evento VARCHAR(10),
            tipo VARCHAR(30) DEFAULT 'evento',
            publico VARCHAR(30) DEFAULT 'todos',
            FOREIGN KEY (id_administrado) REFERENCES adm(id_administrado)
        )
    """)

    # Migração suave para um atlas.db criado pela versão antiga.
    _garantir_coluna(cursor, "eventos", "data_evento", "VARCHAR(10)")
    _garantir_coluna(cursor, "eventos", "tipo", "VARCHAR(30) DEFAULT 'evento'")
    _garantir_coluna(cursor, "eventos", "publico", "VARCHAR(30) DEFAULT 'todos'")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aluno_materia (
            id_aluno INTEGER,
            id_materia INTEGER,
            PRIMARY KEY (id_aluno, id_materia),
            FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno) ON DELETE CASCADE,
            FOREIGN KEY (id_materia) REFERENCES materias(id_materia) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_turma (
            id_professor INTEGER,
            id_turma INTEGER,
            PRIMARY KEY (id_professor, id_turma),
            FOREIGN KEY (id_professor) REFERENCES professor(id_professor) ON DELETE CASCADE,
            FOREIGN KEY (id_turma) REFERENCES turmas(id_turma) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_materia (
            id_professor INTEGER,
            id_materia INTEGER,
            PRIMARY KEY (id_professor, id_materia),
            FOREIGN KEY (id_professor) REFERENCES professor(id_professor) ON DELETE CASCADE,
            FOREIGN KEY (id_materia) REFERENCES materias(id_materia) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turma_materia (
            id_turma INTEGER,
            id_materia INTEGER,
            PRIMARY KEY (id_turma, id_materia),
            FOREIGN KEY (id_turma) REFERENCES turmas(id_turma) ON DELETE CASCADE,
            FOREIGN KEY (id_materia) REFERENCES materias(id_materia) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_evento (
            id_professor INTEGER,
            id_evento INTEGER,
            PRIMARY KEY (id_professor, id_evento),
            FOREIGN KEY (id_professor) REFERENCES professor(id_professor) ON DELETE CASCADE,
            FOREIGN KEY (id_evento) REFERENCES eventos(id_evento) ON DELETE CASCADE
        )
    """)

    # Novas tabelas -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            login VARCHAR(120) NOT NULL UNIQUE,
            senha_hash VARCHAR(255) NOT NULL,
            papel VARCHAR(20) NOT NULL CHECK (papel IN ('aluno', 'professor', 'adm')),
            id_referencia INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS publicacoes (
            id_publicacao INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo VARCHAR(100) NOT NULL,
            descricao VARCHAR(700),
            tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('atividade', 'material', 'aviso')),
            data_publicacao VARCHAR(10) NOT NULL,
            prazo_entrega VARCHAR(10),
            id_professor INTEGER NOT NULL,
            id_turma INTEGER NOT NULL,
            id_materia INTEGER NOT NULL,
            FOREIGN KEY (id_professor) REFERENCES professor(id_professor) ON DELETE CASCADE,
            FOREIGN KEY (id_turma) REFERENCES turmas(id_turma) ON DELETE CASCADE,
            FOREIGN KEY (id_materia) REFERENCES materias(id_materia) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS publicacao_imagens (
            id_imagem INTEGER PRIMARY KEY AUTOINCREMENT,
            id_publicacao INTEGER NOT NULL,
            nome_original VARCHAR(255) NOT NULL,
            mime_type VARCHAR(50) NOT NULL,
            dados BLOB NOT NULL,
            ordem INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (id_publicacao) REFERENCES publicacoes(id_publicacao) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_publicacao_imagens_publicacao
        ON publicacao_imagens(id_publicacao, ordem)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aluno_publicacao (
            id_aluno INTEGER NOT NULL,
            id_publicacao INTEGER NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'progress', 'done')),
            entregue_em VARCHAR(10),
            PRIMARY KEY (id_aluno, id_publicacao),
            FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno) ON DELETE CASCADE,
            FOREIGN KEY (id_publicacao) REFERENCES publicacoes(id_publicacao) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS atividades_pessoais (
            id_atividade INTEGER PRIMARY KEY AUTOINCREMENT,
            id_aluno INTEGER NOT NULL,
            titulo VARCHAR(90) NOT NULL,
            disciplina VARCHAR(150) NOT NULL,
            professor_nome VARCHAR(100),
            prazo VARCHAR(10) NOT NULL,
            descricao VARCHAR(500),
            foi_passada_em_sala INTEGER NOT NULL DEFAULT 1,
            data_passada VARCHAR(10),
            status VARCHAR(20) NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'progress', 'done')),
            entregue_em VARCHAR(10),
            criada_em VARCHAR(10) NOT NULL,
            FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS avisos_aluno (
            id_aviso INTEGER PRIMARY KEY AUTOINCREMENT,
            id_aluno INTEGER NOT NULL,
            titulo VARCHAR(120) NOT NULL,
            data_aviso VARCHAR(10) NOT NULL,
            FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno) ON DELETE CASCADE
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_publicacoes_turma ON publicacoes(id_turma)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_publicacoes_professor ON publicacoes(id_professor)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventos_data ON eventos(data_evento)")

    # Em uma instalação nova, somente adm recebe um registro inicial.
    # Dados já existentes não são apagados por esta inicialização.
    _seed_dados(cursor)
    conexao.commit()
    conexao.close()


if __name__ == "__main__":
    # Permite inicializar o banco executando este arquivo diretamente.
    criar_banco()

"""Exibe todos os registros das tabelas do banco SQLite do projeto."""

from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).resolve().parent / "database" / "atlas.db"


def mostrar_registros():
    """Consulta e imprime as linhas de cada tabela do banco."""
    if not DB_PATH.is_file():
        print(f"Banco de dados não encontrado: {DB_PATH}")
        return

    with sqlite3.connect(DB_PATH) as conexao:
        conexao.row_factory = sqlite3.Row
        tabelas = conexao.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()

        if not tabelas:
            print("O banco não contém tabelas.")
            return

        for (nome_tabela,) in tabelas:
            # Aspas duplas escapadas permitem usar com segurança o nome da tabela.
            tabela_sql = '"' + nome_tabela.replace('"', '""') + '"'
            registros = conexao.execute(f"SELECT * FROM {tabela_sql}").fetchall()

            print(f"\nTabela: {nome_tabela}")
            if not registros:
                print("  (sem registros)")
                continue

            for registro in registros:
                print("  " + repr(dict(registro)))


if __name__ == "__main__":
    mostrar_registros()

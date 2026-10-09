from datetime import timedelta
from pathlib import Path
import os

from flask import Flask, jsonify, redirect, render_template, session
from werkzeug.exceptions import RequestEntityTooLarge


# Pasta raiz do projeto: Atlas-Ceep/
BASE_DIR = Path(__file__).resolve().parent.parent

# Pastas do frontend
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


try:
    from .database.database import criar_banco
    from .routes import registrar_rotas
except ImportError:
    import sys

    sys.path.insert(0, str(BASE_DIR))

    from backend.database.database import criar_banco
    from backend.routes import registrar_rotas


def create_app():
    app = Flask(
        __name__,
        template_folder=str(TEMPLATES_DIR),
        static_folder=str(STATIC_DIR),
        static_url_path="/static",
    )

    app.config.update(
        SECRET_KEY=os.environ.get(
            "ATLAS_SECRET_KEY",
            "atlas-dev-change-this-key"
        ),
        MAX_CONTENT_LENGTH=26 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        JSON_AS_ASCII=False,
    )

    # Inicializa o banco
    criar_banco()

    # Registra as rotas da API
    registrar_rotas(app)

    @app.errorhandler(RequestEntityTooLarge)
    def arquivo_muito_grande(_erro):
        return jsonify({"erro": "O envio excede o limite total de 26 MB."}), 413

    def pagina_para_papel(papel):
        return {
            "aluno": "/aluno",
            "professor": "/professor",
            "adm": "/adm",
        }.get(papel, "/login")

    @app.get("/")
    def home():
        if session.get("papel"):
            return redirect(
                pagina_para_papel(session.get("papel"))
            )

        return redirect("/login")

    @app.get("/login")
    def pagina_login():
        if session.get("papel"):
            return redirect(
                pagina_para_papel(session.get("papel"))
            )

        return render_template("login.html")

    @app.get("/aluno")
    def pagina_aluno():
        if session.get("papel") != "aluno":
            return redirect("/login")

        return render_template("index.html")

    @app.get("/professor")
    def pagina_professor():
        if session.get("papel") != "professor":
            return redirect("/login")

        return render_template("professor.html")

    @app.get("/adm")
    def pagina_adm():
        if session.get("papel") != "adm":
            return redirect("/login")

        return render_template("adm.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

"""Registro dos blueprints da API."""

from .geral import bp as geral_bp
from .auth import bp as auth_bp
from .adms import bp as adms_bp
from .turmas import bp as turmas_bp
from .alunos import bp as alunos_bp
from .professores import bp as professores_bp
from .materias import bp as materias_bp
from .eventos import bp as eventos_bp
from .publicacoes import bp as publicacoes_bp
from .agenda import bp as agenda_bp

BLUEPRINTS = (
    geral_bp,
    auth_bp,
    adms_bp,
    turmas_bp,
    alunos_bp,
    professores_bp,
    materias_bp,
    eventos_bp,
    publicacoes_bp,
    agenda_bp,
)


def registrar_rotas(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint, url_prefix="/api")

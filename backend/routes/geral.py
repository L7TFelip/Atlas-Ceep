from flask import Blueprint, jsonify

bp = Blueprint("geral", __name__)


@bp.get("/")
def inicio():
    return jsonify({"mensagem": "API Atlas CEEP funcionando!", "banco": "atlas.db"})

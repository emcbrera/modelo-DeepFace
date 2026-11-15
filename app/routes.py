import os
import tempfile

from flask import Blueprint, current_app, jsonify, request

from app.auth import requiere_token
from app.validador_expresion import validar_expresion_neutral

api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")


@api_v1.route("/validar-expresion", methods=["POST"])
@requiere_token
def validar_expresion():
    archivo = request.files.get("foto")

    if archivo is None or archivo.filename == "":
        return jsonify({"error": "No se recibió ninguna foto"}), 400

    extension = os.path.splitext(archivo.filename)[1]
    ruta_temporal = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            archivo.save(tmp.name)
            ruta_temporal = tmp.name

        resultado = validar_expresion_neutral(ruta_temporal)
        return jsonify(resultado), 200

    except Exception:
        current_app.logger.exception("Error al procesar la imagen")
        return jsonify({"error": "Error al procesar la imagen"}), 500

    finally:
        if ruta_temporal and os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)

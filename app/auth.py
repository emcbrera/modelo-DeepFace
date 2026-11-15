import hmac
from functools import wraps

from flask import jsonify, request

from app.config import Config


def requiere_token(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "No autorizado"}), 401

        token = auth_header[len("Bearer "):].strip()

        if not hmac.compare_digest(token, Config.TOKEN_API):
            return jsonify({"error": "No autorizado"}), 401

        return f(*args, **kwargs)

    return decorador

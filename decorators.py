from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt
from database import role_has_permission

def permission_required(required_permission):
    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            role = claims.get("role")

            if role is None:
                return jsonify({
                    "message": "Role missing from token"
                }), 403

            if not role_has_permission(role, required_permission):
                return jsonify({
                    "message": "Forbidden",
                    "required_permission": required_permission
                }), 403

            return func(*args, **kwargs)

        return wrapper

    return decorator
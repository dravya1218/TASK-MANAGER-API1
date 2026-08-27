import os

from dotenv import load_dotenv
from flask import Flask,jsonify,request
from flask_jwt_extended import decode_token
from extensions import jwt
from datetime import timedelta
from validators import *
from routes.task_routes import *
from routes.task_routes import task_bp
from task_services import initialize_database
from routes.auth_routes import auth_bp 
from extensions import block_list
from routes.admin_routes import admin_bp
from routes.frontend_routes import frontend_bp
load_dotenv()

app=Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

if not app.config["JWT_SECRET_KEY"]:
    raise ValueError("JWT_SECRET_KEY is missing from the .env file")

initialize_database()
app.config["JWT_ACCESS_TOKEN_EXPIRES"]=timedelta(minutes=30)
jwt.init_app(app)

@app.before_request
def reject_password_reset_tokens_as_session():
    if request.path == "/api/reset-password":
        return None

    auth = request.headers.get("Authorization", "")
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    try:
        claims = decode_token(parts[1])
    except Exception:
        return None

    if claims.get("purpose") == "password_reset":
        return jsonify({
            "error": "Invalid password reset token"
        }), 403

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header,jwt_payload):
    jti=jwt_payload["jti"]
    return jti in block_list

@jwt.expired_token_loader
def expired_token_callback(jwt_header,jwt_payload):
    return jsonify({
        "message":"access token has expired"
    }),401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        "message":"authorization header is missing"
    }),401

@jwt.revoked_token_loader
def revoked_tokrn_callback(jwt_header,jwt_payload):
    return jsonify({
        "message":"token has been revoked. Please login again"
    }),401

@jwt.needs_fresh_token_loader
def needs_fresh_callback(jwt_header,jwt_payload):
    return jsonify({
        "message":"fresh login required"
    }),401

app.register_blueprint(frontend_bp)
app.register_blueprint(task_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
if __name__=="__main__":
    app.run(debug=True)

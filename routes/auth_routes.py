from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from validators import *
from task_services import *
from flask_jwt_extended import get_jwt
from  extensions import block_list

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    error = validate_registration_data(data)
    if error:
        return jsonify({"error": error}), 400

    error, user = registration_user_service(data)
    if error:
        return jsonify({"error": error}), 409

    return jsonify({
        "message": "User registered successfully",
        "user": user
    }), 201


@auth_bp.route("/api/resend-verification", methods=["POST"])
def resend_verification():

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    email = data.get("email")

    if not email:
        return jsonify({
            "error": "Email is required"
        }), 400

    error = resend_email_verification_otp(email)

    if error:
        return jsonify({
            "error": error
        }), 400

    return jsonify({
        "message": "A new verification OTP has been sent"
    }), 200


@auth_bp.route("/api/verify-email", methods=["POST"])
def verify_email():

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    email = data.get("email")
    otp = data.get("otp")

    if not email:
        return jsonify({
            "error": "Email is required"
        }), 400

    if not otp:
        return jsonify({
            "error": "OTP is required"
        }), 400

    if not isinstance(otp, str):
        return jsonify({
            "error": "OTP must be a string"
        }), 400

    if not otp.isdigit() or len(otp) != 6:
        return jsonify({
            "error": "OTP must be a 6-digit number"
        }), 400

    error = verify_email_by_otp_service(
        email,
        otp
    )

    if error:
        return jsonify({
            "error": error
        }), 400

    return jsonify({
        "message": "Email verified successfully"
    }), 200


@auth_bp.route("/api/forgot-password", methods=["POST"])
def forgot_password():

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    email = data.get("email")

    if not email:
        return jsonify({
            "error": "Email is required"
        }), 400

    error = request_password_reset_otp(email)

    if error:
        return jsonify({
            "error": error
        }), 400

    return jsonify({
        "message": "Password reset OTP sent successfully"
    }), 200


@auth_bp.route("/api/verify-password-reset", methods=["POST"])
def verify_password_reset():

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    email = data.get("email")
    otp = data.get("otp")

    if not email:
        return jsonify({
            "error": "Email is required"
        }), 400

    if not otp:
        return jsonify({
            "error": "OTP is required"
        }), 400

    error, reset_token = verify_password_reset_otp_service(
        email,
        otp
    )

    if error:
        return jsonify({
            "error": error
        }), 400

    return jsonify({
        "message": "Password reset OTP verified successfully",
        "reset_token": reset_token
    }), 200


@auth_bp.route("/api/reset-password", methods=["POST"])
@jwt_required()
def reset_password():

    claims = get_jwt()

    if claims.get("purpose") != "password_reset":
        return jsonify({
            "error": "Invalid password reset token"
        }), 403

    user_id = get_jwt_identity()

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not new_password:
        return jsonify({
            "error": "New password is required"
        }), 400

    if not confirm_password:
        return jsonify({
            "error": "Confirm password is required"
        }), 400

    if new_password != confirm_password:
        return jsonify({
            "error": "Passwords do not match"
        }), 400

    if len(new_password) < 6:
        return jsonify({
            "error": "Password must be at least 6 characters"
        }), 400

    error = reset_password_service(
        user_id,
        new_password
    )

    if error:
        return jsonify({
            "error": error
        }), 500

    return jsonify({
        "message": "Password reset successfully"
    }), 200


@auth_bp.route("/api/verify-email-change", methods=["POST"])
@jwt_required()
def verify_email_change():

    user_id = get_jwt_identity()

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    otp = data.get("otp")

    if not otp:
        return jsonify({
            "error": "OTP is required"
        }), 400

    error = verify_email_change_otp_service(
        user_id,
        otp
    )

    if error:
        return jsonify({
            "error": error
        }), 400

    return jsonify({
        "message": "Email changed successfully"
    }), 200


@auth_bp.route("/api/resend-email-change", methods=["POST"])
@jwt_required()
def resend_email_change():

    user_id = get_jwt_identity()

    error = resend_email_change_otp(user_id)

    if error:
        return jsonify({
            "error": error
        }), 400

    return jsonify({
        "message": "Email change OTP sent successfully"
    }), 200


@auth_bp.route("/api/login",methods=["GET","POST"])
def login():
    
    data=request.get_json(silent=True)
    error=validate_login_data(data)
    if error:
        return jsonify({"error":error}),401
    error,token=login_user_service(data)
    if error:
        return jsonify({"error":error}),401
    return jsonify({
        "message": "User login successfully",
        "token":token
    }), 201


@auth_bp.route("/api/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():

    user_id = get_jwt_identity()
    role = get_jwt().get("role")

    access_token = refresh_access_token(user_id, role)

    return jsonify(access_token), 200

@auth_bp.route("/api/logout",methods=["POST"])
@jwt_required()
def logout():
    payload=get_jwt()
    jti=payload["jti"]
    block_list.add(jti)
    return jsonify({"message":"access token revoked"}),200


@auth_bp.route("/api/logout/refresh",methods=["POST"])
@jwt_required(refresh=True)
def logout_refresh():
    payload=get_jwt()
    jti=payload["jti"]
    block_list.add(jti)
    return jsonify({"message":"refresh token revoked"}),200


@auth_bp.route("/api/change-password", methods=["POST"])
@jwt_required()
def change_password():

    user_id = get_jwt_identity()
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "JSON body is required"}), 400

    current_password = data.get("current_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not all(isinstance(password, str) and password for password in [
        current_password,
        new_password,
        confirm_password
    ]):
        return jsonify({"error": "All password fields are required"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    error = change_password_service(
        user_id,
        current_password,
        new_password
    )

    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "message":"Password changed successfully"
    }), 200


@auth_bp.route("/api/profile", methods=["GET"])
@jwt_required()
def get_profile():

    user_id = get_jwt_identity()

    error, user = get_profile_service(user_id)

    if error:
        return jsonify({"error": error}), 404

    return jsonify(user), 200



@auth_bp.route("/api/profile", methods=["PUT"])
@jwt_required()
def update_profile():

    user_id = get_jwt_identity()

    data = request.get_json(silent=True)

    error, result = update_profile_service(user_id, data)

    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "message": result["message"],
        "user": result["user"],
        "email_verification_required": result[
            "email_verification_required"
        ]
    }), 200

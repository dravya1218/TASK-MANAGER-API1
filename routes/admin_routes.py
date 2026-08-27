from flask import Blueprint, jsonify, request,render_template
from flask_jwt_extended import get_jwt_identity, jwt_required
from decorators import permission_required
from task_services import *
admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")


@admin_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
@permission_required("delete_user")
def remove_user(user_id):

    current_user_id = get_jwt_identity()

    if str(current_user_id) == str(user_id):
        return jsonify({
            "error": "You cannot delete your own account."
        }), 400

    error, result = delete_user_service(user_id)

    if error:
        return jsonify({"error": error}), 404

    return jsonify(result), 200

@admin_bp.post("/api/assign_permission")
@jwt_required()
@permission_required("manage_roles")
def assign_permission():
    data=request.get_json()
    role_name=data.get("role_name")
    permission_name=data.get("permission_name")
    result=assign_permission_to_role(role_name,permission_name)
    return jsonify({
        "message":result
    }),200

@admin_bp.delete("/api/remove_permission")
@jwt_required()
@permission_required("manage_roles")
def remove_permission():
    data=request.get_json()
    role_name=data.get("role_name")
    permission_name=data.get("permission_name")
    result=remove_permission_from_role(role_name,permission_name)
    return jsonify({
        "message":result
    }),200

@admin_bp.route("/api/users", methods=["GET"])
@jwt_required()
@permission_required("view_all_users")
def get_users():

    error, users = get_all_users_service()

    if error:
        return jsonify({"error": error}), 404

    return jsonify(users), 200


@admin_bp.route("/api/users/<int:user_id>/role", methods=["PUT"])
@jwt_required()
@permission_required("manage_roles")
def change_user_role(user_id):

    current_user_id = get_jwt_identity()

    # Prevent admin from changing their own role
    if str(current_user_id) == str(user_id):

        return jsonify({
            "error": "You cannot change your own role."
        }), 400

    data = request.get_json()

    role = data.get("role")

    if role not in ["admin", "user"]:

        return jsonify({
            "error": "Invalid role."
        }), 400

    error, result = update_user_role_service(user_id, role)

    if error:

        return jsonify({
            "error": error
        }), 404

    return jsonify(result), 200

@admin_bp.route("/api/admin/roles-permissions", methods=["GET"])
@jwt_required()
@permission_required("manage_roles")
def get_roles_permissions():

    error, result = get_roles_and_permissions_service()

    if error:
        return jsonify({
            "error": error
        }), 404

    return jsonify(result), 200



@admin_bp.route("/api/admin/roles/<role_name>/permissions", methods=["GET"])
@jwt_required()
@permission_required("manage_roles")
def get_role_permissions(role_name):

    error, permissions = get_role_permissions_service(role_name)

    if error:
        return jsonify({"error": error}), 404

    return jsonify(permissions), 200


@admin_bp.route("/api/admin/roles/<role_name>/permissions", methods=["PUT"])
@jwt_required()
@permission_required("manage_roles")
def update_role_permissions(role_name):

    data = request.get_json()

    permissions = data.get("permissions", [])

    error, message = update_role_permissions_service(
        role_name,
        permissions
    )

    if error:

        return jsonify({
            "error": error
        }), 400

    return jsonify({
        "message": message
    }), 200
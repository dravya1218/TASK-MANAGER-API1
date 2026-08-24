from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from task_services import *
from validators import validate_task_data

allowed_sort_feild=["id","priority","status"]
allowed_order=["asc","desc"]
allowed_status=["pending","completed"]
allowed_priority=["high","medium","low"]

task_bp = Blueprint("task", __name__)


@task_bp.route("/api/tasks", methods=["POST"])
@jwt_required()
def create_task():

    user_id = get_jwt_identity()

    data = request.get_json()

    error = validate_task_data(data)

    if error:
        return jsonify({"error": error}), 400

    error, task = create_task_service(user_id, data)

    if error:
        return jsonify({"error": error}), 400

    return jsonify(task), 201

@task_bp.route("/api/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    user_id=get_jwt_identity()
    print(user_id)
    page=request.args.get("page",1,type=int)
    limit=request.args.get("limit",10,type=int)
    sort_by=request.args.get("sort_by","id")
    order=request.args.get("order","asc")
    search=request.args.get("search","").lower().strip()
    status=request.args.get("status","").lower().strip()
    priority=request.args.get("priority","").lower().strip()
    
    if len(search) > 100:
        return jsonify({
            "error":"search querey too long"
        }),400
    if priority and priority not in allowed_priority:
        return jsonify({
            "error":"invalid priority"
        }),400
    if status and status not in allowed_status:
        return jsonify({
            "error":"invalid status"
        }),400

    if page is None or page < 1:
        return jsonify({
            "error":"page must be an positive integer"
        }),400
    if limit is None or limit < 1 or limit > 20:
        return jsonify({
            "error":"limit must be an positive integer and 1-20 "
        }),400
    
    if sort_by not in allowed_sort_feild:
        return jsonify({
            "error":"invalid sort feild"
        }),400
    if order not in allowed_order:
        return jsonify({
            "error":"invalid order"
        }),400

    tasks = get_all_tasks_service(user_id,page,limit,sort_by,order,search,status,priority)

    return jsonify(tasks), 200


@task_bp.route("/api/tasks/<int:id>", methods=["GET"])
@jwt_required()
def get_task(id):
    user_id=get_jwt_identity()
    error, task = get_task_by_id_service(user_id,id)

    if error:
        return jsonify({"error": error}), 404

    return jsonify(task), 200


@task_bp.route("/api/tasks/<int:id>", methods=["PUT"])
@jwt_required()
def update_task(id):
    user_id=get_jwt_identity()
    data = request.get_json()

    error = validate_task_data(data)
    if error:
        return jsonify({"error": error}), 400

    error, task = update_task_service(user_id,id,data)
    if error:
        return jsonify({"error": error}), 404

    return jsonify(task), 200


@task_bp.route("/api/tasks/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_task(id):
    user_id=get_jwt_identity()
    error, result = delete_task_service(user_id,id)

    if error:
        return jsonify({"error": error}), 404

    return jsonify(result), 200


@task_bp.route("/api/categories", methods=["GET"])
@jwt_required()
def get_categories():

    user_id = get_jwt_identity()

    error, categories = get_categories_service(user_id)

    if error:

        return jsonify({
            "error": error
        }), 400

    return jsonify(categories), 200

@task_bp.route("/api/categories", methods=["POST"])
@jwt_required()
def create_category():

    user_id = get_jwt_identity()

    data = request.get_json()

    error, result = create_category_service(
        user_id,
        data
    )

    if error:

        return jsonify({
            "error": error
        }), 400

    return jsonify(result), 201

@task_bp.route("/api/categories/<int:category_id>", methods=["DELETE"])
@jwt_required()
def delete_category_route(category_id):

    user_id = get_jwt_identity()

    error, result = delete_category_service(
        user_id,
        category_id
    )

    if error:
        return jsonify({ 
            "error": error
        }), 400

    return jsonify(result), 200
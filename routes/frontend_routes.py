from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend_bp", __name__)

@frontend_bp.route("/", methods=["GET"])
def home():
    return render_template("login.html")


@frontend_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@frontend_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")


@frontend_bp.route("/dashboard", methods=["GET"])
def dashboard_page():
    return render_template("dashboard.html")


@frontend_bp.route("/profile", methods=["GET"])
def profile_page():
    return render_template("profile.html")

@frontend_bp.route("/manage-permissions", methods=["GET"])
def manage_permissions():

    return render_template(
        "manage_permissions.html"
    )

@frontend_bp.route("/forgot_password", methods=["GET"])
def forgot_password():

    return render_template(
        "forgot_password.html"
    )

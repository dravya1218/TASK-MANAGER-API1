from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend_bp", __name__)

@frontend_bp.route("/")
def home():
    return render_template("login.html")


@frontend_bp.route("/login")
def login_page():
    return render_template("login.html")


@frontend_bp.route("/register")
def register_page():
    return render_template("register.html")


@frontend_bp.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@frontend_bp.route("/profile")
def profile_page():
    return render_template("profile.html")

@frontend_bp.route("/manage-permissions")
def manage_permissions():

    return render_template(
        "manage_permissions.html"
    )

@frontend_bp.route("/forgot_password")
def forgot_password():

    return render_template(
        "forgot_password.html"
    )

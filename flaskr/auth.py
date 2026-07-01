import functools
import sqlite3
from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

BEACHES = [
    "Palm Beach",
    "Whale Beach",
    "Avalon Beach",
    "Bilgola Beach",
    "Newport Beach",
    "Bungan Beach",
    "Mona Vale Beach",
    "Mona Vale Basin",
    "Warriewood Beach",
    "Turimetta Beach",
    # Narrabeen / Collaroy system
    "North Narrabeen Beach",
    "Narrabeen Beach",
    "South Narrabeen Beach",
    "Collaroy Beach",
    # Long Reef area
    "Fishermans Beach",
    "Long Reef Beach",
    # Dee Why
    "North Dee Why Beach",
    "Dee Why Beach",
    "South Dee Why Beach",
    # Curl Curl
    "North Curl Curl Beach",
    "South Curl Curl Beach",
    # Freshwater
    "Freshwater Beach",
]


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                error = f"User {username} already exists."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None

        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("report.main"))

        flash(error)

    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("report.main"))


@bp.route("/profile", methods=("GET", "POST"))
def profile():
    if g.user is None:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        preferred = request.form["preferred_beach"]
        db = get_db()
        db.execute(
            "UPDATE user SET preferred_beach = ? WHERE id = ?",
            (preferred, g.user["id"]),
        )
        db.commit()
        flash("Profile updated.")

    return render_template("auth/profile.html", beaches=BEACHES)


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
from .auth import login_required
from .db import get_db

bp = Blueprint("report", __name__, url_prefix="/report")

SHARK_TYPES = ["Great White", "Tiger Shark", "Hammerhead", "Bull Shark"]
BEACHES = ["Bondi Beach", "Manly Beach", "Coogee Beach", "Palm Beach"]


def cleanup_old_reports(db):
    db.execute("DELETE FROM report WHERE created < datetime('now', '-7 days')")
    db.commit()


@bp.route("/main")
def index():
    print("In report index")
    db = get_db()
    cleanup_old_reports(db)

    reports = db.execute(
        "SELECT r.id, shark_type, beach, size, created, author_id, username "
        "FROM report r JOIN user u ON r.author_id = u.id "
        "ORDER BY created DESC"
    ).fetchall()

    if g.user and g.user["preferred_beach"]:
        for r in reports:
            if r["beach"] == g.user["preferred_beach"]:
                flash("Alert: A shark was reported at your preferred beach!")
                break

    return render_template("report/index.html", reports=reports)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    print("In create")
    if request.method == "POST":
        shark_type = request.form["shark_type"]
        beach = request.form["beach"]
        size = request.form.get("size") or "Unknown"

        db = get_db()
        db.execute(
            "INSERT INTO report (shark_type, beach, size, author_id) VALUES (?, ?, ?, ?)",
            (shark_type, beach, size, g.user["id"]),
        )
        db.commit()
        return redirect(url_for("report.index"))

    return render_template("report/create.html", sharks=SHARK_TYPES, beaches=BEACHES)


def get_report(id, check_author=True):
    report = (
        get_db()
        .execute(
            "SELECT r.id, shark_type, beach, size, created, author_id, username "
            "FROM report r JOIN user u ON r.author_id = u.id WHERE r.id = ?",
            (id,),
        )
        .fetchone()
    )

    if report is None:
        abort(404)

    if check_author and report["author_id"] != g.user["id"]:
        abort(403)

    return report


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    report = get_report(id)

    if request.method == "POST":
        shark_type = request.form["shark_type"]
        beach = request.form["beach"]
        size = request.form.get("size") or "Unknown"

        db = get_db()
        db.execute(
            "UPDATE report SET shark_type = ?, beach = ?, size = ? WHERE id = ?",
            (shark_type, beach, size, id),
        )
        db.commit()
        return redirect(url_for("report.index"))

    return render_template(
        "report/update.html", report=report, sharks=SHARK_TYPES, beaches=BEACHES
    )


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_report(id)
    db = get_db()
    db.execute("DELETE FROM report WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("report.index"))

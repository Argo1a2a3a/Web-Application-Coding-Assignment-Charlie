from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
from .auth import login_required
from .db import get_db

bp = Blueprint("report", __name__)

SHARK_TYPES = [
    "Great White",
    "Tiger Shark",
    "Hammerhead Shark",
    "Bull Shark",
    "Mako Shark",
    "Goblin Shark",
    "Whale Shark",
    "Nurse Shark",
    "Lemon Shark",
    "Blue Shark",
    "Thresher Shark",
    "Basking Shark",
    "Sand Tiger Shark",
    "Blacktip Shark",
    "Silvertip Shark",
    "Oceanic Whitetip Shark",
    "Greenland Shark",
    "Porbeagle Shark",
    "Zebra Shark",
    "Cookiecutter Shark",
    "Wobbegong Shark",
    "Port Jackson Shark",
    "Carpet Shark",
    "Angel Shark",
    "Not listed",
    "Unknown",
    "",
    "",
    "",
    "",
]

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
    "North Narrabeen Beach",
    "Narrabeen Beach",
    "South Narrabeen Beach",
    "Collaroy Beach",
    "Fishermans Beach",
    "Long Reef Beach",
    "North Dee Why Beach",
    "Dee Why Beach",
    "South Dee Why Beach",
    "North Curl Curl Beach",
    "South Curl Curl Beach",
    "Freshwater Beach",
    "Not listed",
    "",
    "",
    "",
    "",
]

DANGER_LEVELS = {
    "Great White": "Very Dangerous",
    "Tiger Shark": "Very Dangerous",
    "Bull Shark": "Very Dangerous",
    "Hammerhead Shark": "Dangerous",
    "Mako Shark": "Dangerous",
    "Oceanic Whitetip Shark": "Dangerous",
    "Sand Tiger Shark": "Moderately Dangerous",
    "Blacktip Shark": "Moderately Dangerous",
    "Silvertip Shark": "Moderately Dangerous",
    "Blue Shark": "Moderately Dangerous",
    "Thresher Shark": "Moderately Dangerous",
    "Basking Shark": "Mostly Harmless",
    "Nurse Shark": "Mostly Harmless",
    "Lemon Shark": "Mostly Harmless",
    "Whale Shark": "Harmless",
    "Wobbegong": "Harmless",
    "Port Jackson Shark": "Harmless",
    "Carpet Shark": "Harmless",
    "Angel Shark": "Harmless",
    "Goblin Shark": "Harmless",
    "Greenland Shark": "Harmless",
    "Porbeagle Shark": "Harmless",
    "Zebra Shark": "Harmless",
    "Cookiecutter Shark": "Harmless",
    "Not listed": "Unknown",
    "Unknown": "Unknown",
}


def cleanup_old_reports(db):
    db.execute("DELETE FROM report WHERE created < datetime('now', '-7 days')")
    db.commit()


@bp.route("/")
def index():
    db = get_db()
    cleanup_old_reports(db)

    query = request.args.get("q", "").strip()

    if query:
        reports = db.execute(
            "SELECT r.id, shark_type, beach, size, danger_level, created, author_id, username "
            "FROM report r JOIN user u ON r.author_id = u.id "
            "WHERE shark_type LIKE ? OR beach LIKE ? OR danger_level LIKE ? "
            "ORDER BY created DESC",
            (f"%{query}%", f"%{query}%", f"%{query}%"),
        ).fetchall()
    else:
        reports = db.execute(
            "SELECT r.id, shark_type, beach, size, danger_level, created, author_id, username "
            "FROM report r JOIN user u ON r.author_id = u.id "
            "ORDER BY created DESC"
        ).fetchall()

    count = len(reports)

    if g.user and g.user["preferred_beach"]:
        for r in reports:
            if r["beach"] == g.user["preferred_beach"]:
                flash("Alert: A shark was reported at your preferred beach!")
                break

    return render_template(
        "report/index.html", reports=reports, count=count, query=query
    )


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        shark_type = request.form["shark_type"]
        beach = request.form["beach"]
        size = request.form.get("size") or "Unknown"

        danger = DANGER_LEVELS.get(shark_type, "Unknown")

        db = get_db()
        db.execute(
            "INSERT INTO report (shark_type, beach, size, danger_level, author_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (shark_type, beach, size, danger, g.user["id"]),
        )
        db.commit()
        return redirect(url_for("report.index"))

    return render_template("report/create.html", sharks=SHARK_TYPES, beaches=BEACHES)


def get_report(id, check_author=True):
    report = (
        get_db()
        .execute(
            "SELECT r.id, shark_type, beach, size, danger_level, created, author_id, username "
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

        danger = DANGER_LEVELS.get(shark_type, "Unknown")

        db = get_db()
        db.execute(
            "UPDATE report SET shark_type = ?, beach = ?, size = ?, danger_level = ? WHERE id = ?",
            (shark_type, beach, size, danger, id),
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

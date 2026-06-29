"""
main.py

Flask application for the charity volunteer & donation tracker.
Routes cover: a dashboard summary, managing people, logging volunteer
hours, and logging donations.
"""

import os
from datetime import date

from flask import Flask, render_template, request, redirect, url_for, flash

from . import repository as repo
from .db import init_db

DB_PATH = os.environ.get("CHARITY_TRACKER_DB", "charity_tracker.db")


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    init_db(DB_PATH)

    @app.route("/")
    def dashboard():
        stats = repo.summary(DB_PATH)
        top_volunteers = repo.total_hours_by_person(DB_PATH)[:5]
        top_donors = repo.total_donations_by_person(DB_PATH)[:5]
        recent_hours = repo.list_hours(db_path=DB_PATH)[:5]
        recent_donations = repo.list_donations(db_path=DB_PATH)[:5]
        return render_template(
            "dashboard.html",
            stats=stats,
            top_volunteers=top_volunteers,
            top_donors=top_donors,
            recent_hours=recent_hours,
            recent_donations=recent_donations,
        )

    # ------------------------------------------------------------------
    # People
    # ------------------------------------------------------------------

    @app.route("/people")
    def people_list():
        people = repo.list_people(DB_PATH)
        return render_template("people.html", people=people)

    @app.route("/people/add", methods=["POST"])
    def people_add():
        try:
            repo.add_person(
                name=request.form.get("name", ""),
                email=request.form.get("email", ""),
                notes=request.form.get("notes", ""),
                db_path=DB_PATH,
            )
            flash("Person added.", "success")
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("people_list"))

    @app.route("/people/<int:person_id>/delete", methods=["POST"])
    def people_delete(person_id):
        repo.delete_person(person_id, db_path=DB_PATH)
        flash("Person removed.", "success")
        return redirect(url_for("people_list"))

    @app.route("/people/<int:person_id>")
    def person_detail(person_id):
        person = repo.get_person(person_id, db_path=DB_PATH)
        if person is None:
            flash("That person doesn't exist.", "error")
            return redirect(url_for("people_list"))
        hours = repo.list_hours(person_id=person_id, db_path=DB_PATH)
        donations = repo.list_donations(person_id=person_id, db_path=DB_PATH)
        hours_total = sum(h["hours"] for h in hours)
        donations_total = sum(d["amount"] for d in donations)
        return render_template(
            "person_detail.html",
            person=person,
            hours=hours,
            donations=donations,
            hours_total=hours_total,
            donations_total=donations_total,
        )

    # ------------------------------------------------------------------
    # Volunteer hours
    # ------------------------------------------------------------------

    @app.route("/hours")
    def hours_list():
        hours = repo.list_hours(db_path=DB_PATH)
        people = repo.list_people(DB_PATH)
        return render_template("hours.html", hours=hours, people=people, today=date.today().isoformat())

    @app.route("/hours/add", methods=["POST"])
    def hours_add():
        try:
            hours_value = float(request.form.get("hours", 0))
            repo.log_hours(
                person_id=int(request.form.get("person_id")),
                activity=request.form.get("activity", ""),
                hours=hours_value,
                date_logged=request.form.get("date_logged") or date.today().isoformat(),
                notes=request.form.get("notes", ""),
                db_path=DB_PATH,
            )
            flash("Volunteer hours logged.", "success")
        except (ValueError, TypeError) as exc:
            flash(f"Couldn't log hours: {exc}", "error")
        return redirect(url_for("hours_list"))

    @app.route("/hours/<int:entry_id>/delete", methods=["POST"])
    def hours_delete(entry_id):
        repo.delete_hours_entry(entry_id, db_path=DB_PATH)
        flash("Entry removed.", "success")
        return redirect(url_for("hours_list"))

    # ------------------------------------------------------------------
    # Donations
    # ------------------------------------------------------------------

    @app.route("/donations")
    def donations_list():
        donations = repo.list_donations(db_path=DB_PATH)
        people = repo.list_people(DB_PATH)
        return render_template(
            "donations.html", donations=donations, people=people, today=date.today().isoformat()
        )

    @app.route("/donations/add", methods=["POST"])
    def donations_add():
        try:
            amount_value = float(request.form.get("amount", 0))
            repo.log_donation(
                person_id=int(request.form.get("person_id")),
                amount=amount_value,
                date_received=request.form.get("date_received") or date.today().isoformat(),
                currency=request.form.get("currency", "GBP"),
                method=request.form.get("method", ""),
                notes=request.form.get("notes", ""),
                db_path=DB_PATH,
            )
            flash("Donation logged.", "success")
        except (ValueError, TypeError) as exc:
            flash(f"Couldn't log donation: {exc}", "error")
        return redirect(url_for("donations_list"))

    @app.route("/donations/<int:entry_id>/delete", methods=["POST"])
    def donations_delete(entry_id):
        repo.delete_donation_entry(entry_id, db_path=DB_PATH)
        flash("Entry removed.", "success")
        return redirect(url_for("donations_list"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

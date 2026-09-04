import argparse
import csv
import io
import os
from functools import wraps
from pathlib import Path

from flask import Flask, Response, redirect, render_template, request, session, url_for

from attendance import AttendanceStore
from auth import AuthStore
from analytics import build_analytics
from roster import RosterStore
from corrections import CorrectionStore


def create_app(database_path: Path) -> Flask:
    app = Flask(__name__)
    app.config.update(
        DATABASE_PATH=database_path,
        SECRET_KEY=os.environ.get("DASHBOARD_SECRET_KEY", "dev-only-change-me"),
    )

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "username" not in session:
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)
        return wrapped

    def stores():
        return AttendanceStore(app.config["DATABASE_PATH"]), AuthStore(app.config["DATABASE_PATH"])

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            attendance_store, auth_store = stores()
            try:
                if auth_store.authenticate(username, password):
                    session.clear()
                    session["username"] = username.strip()
                    auth_store.audit(username, "login")
                    return redirect(request.args.get("next") or url_for("index"))
            finally:
                attendance_store.close()
                auth_store.close()
            return render_template("login.html", error="Invalid username or password.")
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        username = session.get("username", "unknown")
        attendance_store, auth_store = stores()
        try:
            auth_store.audit(username, "logout")
        finally:
            attendance_store.close()
            auth_store.close()
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def index():
        store, auth_store = stores()
        try:
            records = store.records()
            return render_template("dashboard.html", people=store.list_people(), sessions=store.list_sessions(), recent_records=records[:10], total=len(records), logs=auth_store.logs(10))
        finally:
            store.close(); auth_store.close()

    @app.get("/people")
    @login_required
    def people():
        store, auth_store = stores()
        try:
            return render_template("people.html", people=store.list_people())
        finally:
            store.close(); auth_store.close()

    @app.post("/people/<int:person_id>/toggle")
    @login_required
    def toggle_person(person_id):
        store, auth_store = stores()
        username = session["username"]
        try:
            person = store.get_person(person_id)
            store.set_person_active(person_id, not person.is_active)
            action = "person_activated" if not person.is_active else "person_deactivated"
            auth_store.audit(username, action, f"person:{person_id}")
        finally:
            store.close(); auth_store.close()
        return redirect(url_for("people"))

    @app.get("/analytics")
    @login_required
    def analytics_view():
        store, auth_store = stores()
        try:
            people_list = store.list_people()
            sessions_list = store.list_sessions()
            metrics = build_analytics(store.records(), people_list, sessions_list)
            return render_template("analytics.html", metrics=metrics)
        finally:
            store.close(); auth_store.close()

    @app.route("/sessions/<int:session_id>/roster", methods=["GET", "POST"])
    @login_required
    def session_roster(session_id):
        store, auth_store = stores()
        roster_store = RosterStore(app.config["DATABASE_PATH"])
        try:
            target_session = store.get_session(session_id)
            people_list = store.list_people(active_only=True)
            if request.method == "POST":
                selected = {int(value) for value in request.form.getlist("person_ids")}
                current = set(roster_store.roster(session_id))
                for person_id in current - selected:
                    roster_store.remove_person(session_id, person_id)
                roster_store.add_all(session_id, list(selected - current))
                auth_store.audit(session["username"], "roster_updated", f"session:{session_id}")
                return redirect(url_for("session_roster", session_id=session_id))
            roster_ids = set(roster_store.roster(session_id))
            present_ids = {record.person_id for record in store.records(session_id)}
            status_rows = [(person, person.id in roster_ids, person.id in present_ids) for person in people_list]
            return render_template("session_roster.html", target_session=target_session, status_rows=status_rows)
        finally:
            roster_store.close(); store.close(); auth_store.close()

    @app.post("/attendance/<int:record_id>/void")
    @login_required
    def void_attendance(record_id):
        reason = request.form.get("reason", "")
        correction_store = CorrectionStore(app.config["DATABASE_PATH"])
        auth_store = AuthStore(app.config["DATABASE_PATH"])
        try:
            correction_store.void_record(record_id, reason, session["username"])
            auth_store.audit(session["username"], "attendance_voided", f"record:{record_id}")
        except ValueError as error:
            return Response(str(error), status=400)
        finally:
            correction_store.close(); auth_store.close()
        return redirect(url_for("attendance"))

    @app.post("/attendance/<int:record_id>/restore")
    @login_required
    def restore_attendance(record_id):
        correction_store = CorrectionStore(app.config["DATABASE_PATH"])
        auth_store = AuthStore(app.config["DATABASE_PATH"])
        try:
            correction_store.restore_record(record_id)
            auth_store.audit(session["username"], "attendance_restored", f"record:{record_id}")
        finally:
            correction_store.close(); auth_store.close()
        return redirect(url_for("attendance"))

    @app.get("/sessions")
    @login_required
    def sessions():
        store, auth_store = stores()
        try:
            return render_template("sessions.html", sessions=store.list_sessions())
        finally:
            store.close(); auth_store.close()

    @app.get("/attendance")
    @login_required
    def attendance():
        store, auth_store = stores()
        correction_store = CorrectionStore(app.config["DATABASE_PATH"])
        try:
            session_id = request.args.get("session_id", type=int)
            session_date = request.args.get("date") or None
            records = store.records(session_id, session_date)
            return render_template("attendance.html", records=records, corrections=correction_store.statuses(), sessions=store.list_sessions(), selected_session=session_id, selected_date=session_date or "")
        finally:
            correction_store.close(); store.close(); auth_store.close()

    @app.get("/attendance/export")
    @login_required
    def export_attendance():
        store, auth_store = stores()
        correction_store = CorrectionStore(app.config["DATABASE_PATH"])
        try:
            records = store.records(request.args.get("session_id", type=int), request.args.get("date") or None)
            corrections = correction_store.statuses()
        finally:
            correction_store.close(); store.close(); auth_store.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["attendance_id", "person_id", "name", "session_id", "date", "time"])
        for record in records:
            if record.id in corrections:
                continue
            writer.writerow([record.id, record.person_id, record.name, record.session_id, record.attendance_date, record.time])
        response = Response(output.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=attendance-report.csv"
        return response

    return app


def main():
    parser = argparse.ArgumentParser(description="Run the protected local attendance dashboard.")
    parser.add_argument("--database", type=Path, default=Path("attendance.db"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    app = create_app(args.database)
    print(f"Dashboard running at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()

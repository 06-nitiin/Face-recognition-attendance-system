import argparse
import csv
import io
import os
from functools import wraps
from pathlib import Path

from flask import Flask, Response, redirect, render_template, request, session, url_for

from attendance import AttendanceStore
from auth import AuthStore


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
        try:
            session_id = request.args.get("session_id", type=int)
            session_date = request.args.get("date") or None
            return render_template("attendance.html", records=store.records(session_id, session_date), sessions=store.list_sessions(), selected_session=session_id, selected_date=session_date or "")
        finally:
            store.close(); auth_store.close()

    @app.get("/attendance/export")
    @login_required
    def export_attendance():
        store, auth_store = stores()
        try:
            records = store.records(request.args.get("session_id", type=int), request.args.get("date") or None)
        finally:
            store.close(); auth_store.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["attendance_id", "person_id", "name", "session_id", "date", "time"])
        for record in records:
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

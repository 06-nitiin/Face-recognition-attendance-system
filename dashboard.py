import argparse
import csv
import io
from pathlib import Path

from flask import Flask, Response, render_template, request, send_file

from attendance import AttendanceStore
from dashboard_utils import attendance_summary, filter_records


def create_app(database_path: Path) -> Flask:
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = database_path

    def get_store():
        return AttendanceStore(app.config["DATABASE_PATH"])

    @app.get("/")
    def index():
        store = get_store()
        try:
            people = store.list_people()
            sessions = store.list_sessions()
            records = store.records()
            summary = attendance_summary(records)
            return render_template(
                "dashboard.html",
                people=people,
                sessions=sessions,
                recent_records=records[:10],
                summary=summary,
            )
        finally:
            store.close()

    @app.get("/people")
    def people():
        store = get_store()
        try:
            return render_template("people.html", people=store.list_people())
        finally:
            store.close()

    @app.get("/sessions")
    def sessions():
        store = get_store()
        try:
            return render_template("sessions.html", sessions=store.list_sessions())
        finally:
            store.close()

    @app.get("/attendance")
    def attendance():
        store = get_store()
        try:
            session_id = request.args.get("session_id", type=int)
            session_date = request.args.get("date") or None
            records = store.records(session_id=session_id, session_date=session_date)
            return render_template(
                "attendance.html",
                records=records,
                sessions=store.list_sessions(),
                selected_session=session_id,
                selected_date=session_date or "",
            )
        finally:
            store.close()

    @app.get("/attendance/export")
    def export_attendance():
        store = get_store()
        try:
            session_id = request.args.get("session_id", type=int)
            session_date = request.args.get("date") or None
            records = store.records(session_id=session_id, session_date=session_date)
        finally:
            store.close()

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
    parser = argparse.ArgumentParser(description="Run the local attendance dashboard.")
    parser.add_argument("--database", type=Path, default=Path("attendance.db"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    app = create_app(args.database)
    print(f"Dashboard running at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()

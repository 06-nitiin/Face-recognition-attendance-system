from collections import Counter


def build_analytics(records, people=None, sessions=None):
    """Return dashboard-friendly attendance metrics from AttendanceRecord objects."""
    people = people or []
    sessions = sessions or []
    session_names = {session.id: session.name for session in sessions}
    person_totals = Counter(record.name for record in records)
    session_totals = Counter(record.session_id for record in records)
    daily_totals = Counter(record.attendance_date for record in records)
    return {
        "total_records": len(records),
        "active_people": sum(person.is_active for person in people),
        "people_totals": sorted(person_totals.items(), key=lambda item: (-item[1], item[0].lower())),
        "session_totals": sorted(
            ((session_names.get(session_id, f"Session #{session_id}"), count) for session_id, count in session_totals.items()),
            key=lambda item: (-item[1], item[0].lower()),
        ),
        "daily_totals": sorted(daily_totals.items(), reverse=True),
    }

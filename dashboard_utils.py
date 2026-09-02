from collections import Counter


def filter_records(records, session_id=None, session_date=None):
    filtered = records
    if session_id is not None:
        filtered = [record for record in filtered if record.session_id == session_id]
    if session_date:
        filtered = [record for record in filtered if record.attendance_date == session_date]
    return filtered


def attendance_summary(records):
    by_date = Counter(record.attendance_date for record in records)
    by_session = Counter(record.session_id for record in records)
    return {
        "total": len(records),
        "dates": len(by_date),
        "sessions": len(by_session),
        "by_date": dict(sorted(by_date.items(), reverse=True)),
    }

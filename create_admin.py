import argparse
import getpass
from pathlib import Path

from auth import AuthStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a local dashboard administrator.")
    parser.add_argument("username")
    parser.add_argument("--database", type=Path, default=Path("attendance.db"))
    args = parser.parse_args()

    password = getpass.getpass("Password (minimum 8 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    store = AuthStore(args.database)
    try:
        admin_id = store.create_admin(args.username, password)
    except ValueError as error:
        raise SystemExit(f"Admin creation error: {error}") from error
    finally:
        store.close()
    print(f"Created admin #{admin_id}.")


if __name__ == "__main__":
    main()

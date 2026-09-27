import argparse

from buildable_authorization import bootstrap_administrator
from buildable_core import create_engine_and_session_factory, get_settings
from buildable_core.errors import AppError
from buildable_identity import UserRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the first authorization administrator.")
    parser.add_argument("--email", required=True, help="Email of an existing verified user.")
    args = parser.parse_args()

    settings = get_settings()
    engine, session_factory = create_engine_and_session_factory(settings.database_url)
    try:
        with session_factory() as session:
            user = UserRepository(session).get_by_email(args.email.strip().lower())
            if user is None:
                raise AppError(
                    "user_not_found", "The requested user was not found.", status_code=404
                )
            role = bootstrap_administrator(session, user.id)
            print(f"Assigned {role.name} to {user.email}.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

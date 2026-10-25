"""Legacy alias for interactive first-admin setup; never resets passwords."""

from bootstrap_admin import main


if __name__ == "__main__":
    raise SystemExit(main())

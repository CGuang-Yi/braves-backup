#!/usr/bin/env python3
"""Dump the backup URI without putting its credentials in argv or diagnostics."""
import os
import subprocess
import sys
from urllib.parse import unquote, urlsplit


def dump_environment(uri):
    parsed = urlsplit(uri)
    if (parsed.scheme not in ("postgresql", "postgres") or not parsed.hostname
            or parsed.username is None or parsed.password is None
            or not parsed.path.startswith("/") or not parsed.path[1:]
            or parsed.fragment):
        raise ValueError("invalid PostgreSQL URI")
    # unquote (not unquote_plus) decodes userinfo exactly once: a literal '+'
    # stays '+', and %2540 becomes the literal '%40', never '@'.
    env = dict(os.environ)
    env.pop("DB_URL", None)
    env.update(
        PGUSER=unquote(parsed.username, errors="strict"),
        PGPASSWORD=unquote(parsed.password, errors="strict"),
        PGHOST=parsed.hostname,
        PGPORT=str(parsed.port or 5432),
        PGDATABASE=unquote(parsed.path[1:], errors="strict"),
        PGSSLMODE="require",
    )
    return env


def main():
    if len(sys.argv) != 2:
        print("Usage: dump.py <output-file>", file=sys.stderr)
        return 1
    try:
        env = dump_environment(os.environ.get("DB_URL", ""))
    except (ValueError, UnicodeError):
        # Parser exceptions may include the input; never print the secret URI.
        print("SUPABASE_DB_URL is not a valid PostgreSQL connection URI", file=sys.stderr)
        return 1
    try:
        result = subprocess.run(
            ["pg_dump", "--schema=public", "--schema=auth", "--schema=private",
             "-Fc", "-f", sys.argv[1]], env=env, capture_output=True, text=True)
    except OSError:
        print("Could not start pg_dump", file=sys.stderr)
        return 1
    # libpq includes the username in authentication failures. Keep useful
    # diagnostics while preventing either userinfo value from reaching logs.
    secrets = sorted({env["PGUSER"], env["PGPASSWORD"]}, key=len, reverse=True)
    for output, destination in ((result.stdout, sys.stdout), (result.stderr, sys.stderr)):
        for secret in secrets:
            if secret:
                output = output.replace(secret, "[redacted]")
        print(output, end="", file=destination)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

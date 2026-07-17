#!/bin/sh
set -e

check_postgres() {
  python - <<'PY'
import os
import time
import psycopg2
from psycopg2 import OperationalError

url = os.getenv('DATABASE_URL')
if not url:
    raise SystemExit('DATABASE_URL is not set')

for attempt in range(20):
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print('PostgreSQL is available')
        raise SystemExit(0)
    except OperationalError as exc:
        print(f'PostgreSQL not ready yet ({attempt + 1}/20): {exc}')
        time.sleep(2)
raise SystemExit(1)
PY
}

check_postgres

alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

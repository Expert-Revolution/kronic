#!/bin/bash
# wait-for-db.sh

set -e

host="$1"
port="$2"
db_name="$3"
user="$4"
password="$5"
shift 5
cmd="$@"

echo "Waiting for PostgreSQL at $host:$port..."

until PGPASSWORD=$password psql -h "$host" -p "$port" -U "$user" -d "$db_name" -c "\q"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec $cmd

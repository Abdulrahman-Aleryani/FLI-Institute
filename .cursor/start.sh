#!/usr/bin/env bash
# Per-boot reconciliation for the Frappe Learning (LMS) environment.
# Brings up MariaDB and Redis, re-establishes the app bind-mount and syncs the
# database schema for the currently checked-out branch. Long-running dev
# servers ('bench start' and the Vite dev server) run in the terminals instead.
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_DIR="$HOME/frappe-bench"
SITE="lms.test"
DB_ROOT_PASSWORD="123"

log() { echo -e "\n==> $*"; }

log "Ensure ${SITE} resolves to localhost"
grep -qxF "127.0.0.1 ${SITE}" /etc/hosts || echo "127.0.0.1 ${SITE}" | sudo tee -a /etc/hosts >/dev/null

log "Start MariaDB"
sudo install -d -o mysql -g mysql /run/mysqld
if ! pgrep -x mariadbd >/dev/null 2>&1; then
	sudo /usr/sbin/mariadbd --user=mysql >/tmp/mariadbd.log 2>&1 &
fi
for _ in $(seq 1 60); do
	mariadb --host 127.0.0.1 -u root -p"$DB_ROOT_PASSWORD" -e "SELECT 1" >/dev/null 2>&1 && break
	sleep 1
done

log "Start Redis (cache :13000, queue :11000)"
redis-cli -p 13000 ping >/dev/null 2>&1 || redis-server --daemonize yes --port 13000 --bind 127.0.0.1 --save '' --appendonly no --dir /tmp
redis-cli -p 11000 ping >/dev/null 2>&1 || redis-server --daemonize yes --port 11000 --bind 127.0.0.1 --save '' --appendonly no --dir /tmp

log "Mount this repository as the 'lms' app"
mkdir -p "$BENCH_DIR/apps/lms"
mountpoint -q "$BENCH_DIR/apps/lms" || sudo mount --bind "$REPO" "$BENCH_DIR/apps/lms"

log "Sync database schema for the current branch"
cd "$BENCH_DIR"
bench --site "$SITE" migrate || echo "WARNING: 'bench migrate' failed; the site keeps its previous schema."

echo -e "\nEnvironment ready. Run the 'bench' and 'frontend-dev' terminals to serve the app."

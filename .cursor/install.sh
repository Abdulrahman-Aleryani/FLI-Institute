#!/usr/bin/env bash
# Idempotent setup for the Frappe Learning (LMS) Cloud Agent environment.
# Builds a Frappe v15 bench, wires this repository in as the `lms` app, creates
# the `lms.test` site and builds all assets. Safe to re-run.
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
export DEBIAN_FRONTEND=noninteractive

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_DIR="$HOME/frappe-bench"
SITE="lms.test"
FRAPPE_BRANCH="version-15"
DB_ROOT_PASSWORD="123"
ADMIN_PASSWORD="admin"

log() { echo -e "\n==> $*"; }

log "[1/9] System dependencies"
if ! command -v mariadbd >/dev/null 2>&1 \
   || ! command -v redis-server >/dev/null 2>&1 \
   || ! command -v wkhtmltopdf >/dev/null 2>&1 \
   || ! command -v crontab >/dev/null 2>&1; then
	sudo apt-get update -y
	sudo apt-get install -y --no-install-recommends \
		mariadb-server mariadb-client libmariadb-dev redis-server \
		wkhtmltopdf libcups2-dev python3-dev python3-venv python3-pip \
		build-essential libffi-dev libssl-dev pkg-config libcairo2 cron pipx
fi

log "[2/9] frappe-bench and uv (via pipx)"
pipx list --short 2>/dev/null | grep -q 'frappe-bench' || pipx install frappe-bench
pipx list --short 2>/dev/null | grep -q '^uv ' || pipx install uv

log "[3/9] Start MariaDB and apply utf8mb4 config"
sudo install -d -o mysql -g mysql /run/mysqld
sudo cp "$REPO/.cursor/mariadb-utf8mb4.cnf" /etc/mysql/mariadb.conf.d/99-frappe-utf8mb4.cnf
if ! pgrep -x mariadbd >/dev/null 2>&1; then
	sudo /usr/sbin/mariadbd --user=mysql >/tmp/mariadbd-install.log 2>&1 &
fi
for _ in $(seq 1 60); do
	sudo mariadb -e "SELECT 1" >/dev/null 2>&1 && break
	mariadb --host 127.0.0.1 -u root -p"$DB_ROOT_PASSWORD" -e "SELECT 1" >/dev/null 2>&1 && break
	sleep 1
done
# Ensure the MariaDB root account authenticates over TCP with a password so
# that bench can connect as root when creating sites.
if ! mariadb --host 127.0.0.1 -u root -p"$DB_ROOT_PASSWORD" -e "SELECT 1" >/dev/null 2>&1; then
	sudo mariadb -e "ALTER USER 'root'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('${DB_ROOT_PASSWORD}'); FLUSH PRIVILEGES;"
fi

log "[4/9] Start Redis (cache :13000, queue :11000) for setup"
redis-cli -p 13000 ping >/dev/null 2>&1 || redis-server --daemonize yes --port 13000 --bind 127.0.0.1 --save '' --appendonly no --dir /tmp
redis-cli -p 11000 ping >/dev/null 2>&1 || redis-server --daemonize yes --port 11000 --bind 127.0.0.1 --save '' --appendonly no --dir /tmp

log "[5/9] Initialise bench (Frappe ${FRAPPE_BRANCH})"
if [ ! -d "$BENCH_DIR/apps/frappe" ]; then
	bench init "$BENCH_DIR" --frappe-branch "$FRAPPE_BRANCH" --skip-assets --python "$(command -v python3)"
fi

log "[6/9] Mount this repository as the 'lms' app and install it (editable)"
mkdir -p "$BENCH_DIR/apps/lms"
# Bind-mount (not symlink) so the app sits at a real path inside the bench.
# The frontend build resolves ../../../../sites relative to apps/lms/frontend.
mountpoint -q "$BENCH_DIR/apps/lms" || sudo mount --bind "$REPO" "$BENCH_DIR/apps/lms"
printf 'frappe\nlms\n' > "$BENCH_DIR/sites/apps.txt"
uv pip install -q -e "$BENCH_DIR/apps/lms" --python "$BENCH_DIR/env/bin/python"

log "[7/9] Install and build the Vue frontend"
( cd "$BENCH_DIR/apps/lms/frontend" && (yarn install --frozen-lockfile || yarn install) && yarn build )

log "[8/9] Create the '${SITE}' site and install the LMS app"
cd "$BENCH_DIR"
if [ ! -d "$BENCH_DIR/sites/$SITE" ]; then
	bench new-site "$SITE" \
		--mariadb-root-password "$DB_ROOT_PASSWORD" \
		--admin-password "$ADMIN_PASSWORD" \
		--mariadb-user-host-login-scope='%'
fi
if ! bench --site "$SITE" list-apps 2>/dev/null | grep -qx lms; then
	bench --site "$SITE" install-app lms
fi
bench --site "$SITE" set-config developer_mode 1
bench --site "$SITE" set-config host_name "http://${SITE}:8000"
# Keep the scheduler enabled so the 'schedule' process in 'bench start' stays
# alive (honcho stops every process if any one of them exits).
bench --site "$SITE" enable-scheduler
bench --site "$SITE" migrate

log "[9/9] Build assets and hand Redis over to the start script"
bench build --app lms
# Redis is managed by .cursor/start.sh (daemonised), so remove it from the
# Procfile to avoid 'address already in use' when 'bench start' runs.
# Also drop 'schedule': it is a short-lived command in this build, and honcho
# stops every process as soon as one exits (matches Frappe's own CI setup).
if [ -f "$BENCH_DIR/Procfile" ]; then
	sed -i '/^redis/d;/^schedule/d' "$BENCH_DIR/Procfile"
fi

echo -e "\nInstall complete. Site: http://${SITE}:8000/lms (Administrator / ${ADMIN_PASSWORD})"

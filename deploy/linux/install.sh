#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [[ "${EUID}" -eq 0 ]]; then
  RUN_AS_ROOT=()
else
  if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo is required when install.sh is not run as root" >&2
    exit 1
  fi
  RUN_AS_ROOT=(sudo)
fi

APP_DIR="${APP_DIR:-/opt/owen-gateway}"
CONFIG_DIR="${CONFIG_DIR:-/etc/owen-gateway}"
SERVICE_NAME="${SERVICE_NAME:-owen-gateway}"
SERVICE_USER="${SERVICE_USER:-owen}"
SERVICE_GROUP="${SERVICE_GROUP:-${SERVICE_USER}}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_ARGS="${VENV_ARGS:---system-site-packages}"
CONFIG_SOURCE="${CONFIG_SOURCE:-${REPO_DIR}/owen_config.linux.json}"
PROBE_CONFIG_SOURCE="${PROBE_CONFIG_SOURCE:-${REPO_DIR}/owen_probe.linux.json}"
SERVICE_TEMPLATE="${SERVICE_TEMPLATE:-${REPO_DIR}/deploy/linux/owen-gateway.service.template}"

if [[ ! -f "${REPO_DIR}/requirements.txt" ]]; then
  echo "requirements.txt not found: ${REPO_DIR}" >&2
  exit 1
fi

if [[ ! -f "${CONFIG_SOURCE}" ]]; then
  echo "config source not found: ${CONFIG_SOURCE}" >&2
  exit 1
fi

if [[ ! -f "${SERVICE_TEMPLATE}" ]]; then
  echo "service template not found: ${SERVICE_TEMPLATE}" >&2
  exit 1
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "python binary not found: ${PYTHON_BIN}" >&2
  exit 1
fi

echo "Installing gateway to ${APP_DIR}"
"${RUN_AS_ROOT[@]}" install -d -m 0755 "${APP_DIR}" "${CONFIG_DIR}"

if ! getent group "${SERVICE_GROUP}" >/dev/null 2>&1; then
  "${RUN_AS_ROOT[@]}" groupadd --system "${SERVICE_GROUP}"
fi

if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  "${RUN_AS_ROOT[@]}" useradd \
    --system \
    --gid "${SERVICE_GROUP}" \
    --home-dir "${APP_DIR}" \
    --create-home \
    --shell /usr/sbin/nologin \
    "${SERVICE_USER}"
fi

"${RUN_AS_ROOT[@]}" rsync -a \
  --delete \
  --exclude '.git' \
  --exclude '.idea' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'tmp_*' \
  --exclude 'archive' \
  "${REPO_DIR}/" "${APP_DIR}/"

"${RUN_AS_ROOT[@]}" "${PYTHON_BIN}" -m venv ${VENV_ARGS} "${APP_DIR}/.venv"
"${RUN_AS_ROOT[@]}" "${APP_DIR}/.venv/bin/pip" install --upgrade pip
"${RUN_AS_ROOT[@]}" "${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

"${RUN_AS_ROOT[@]}" install -m 0644 "${CONFIG_SOURCE}" "${CONFIG_DIR}/owen_config.json"
if [[ -f "${PROBE_CONFIG_SOURCE}" ]]; then
  "${RUN_AS_ROOT[@]}" install -m 0644 "${PROBE_CONFIG_SOURCE}" "${CONFIG_DIR}/owen_probe.json"
fi

TMP_UNIT="$(mktemp)"
sed \
  -e "s|@APP_DIR@|${APP_DIR}|g" \
  -e "s|@CONFIG_DIR@|${CONFIG_DIR}|g" \
  -e "s|@SERVICE_USER@|${SERVICE_USER}|g" \
  -e "s|@SERVICE_GROUP@|${SERVICE_GROUP}|g" \
  "${SERVICE_TEMPLATE}" > "${TMP_UNIT}"
"${RUN_AS_ROOT[@]}" install -m 0644 "${TMP_UNIT}" "/etc/systemd/system/${SERVICE_NAME}.service"
rm -f "${TMP_UNIT}"

"${RUN_AS_ROOT[@]}" chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${APP_DIR}" "${CONFIG_DIR}"

"${RUN_AS_ROOT[@]}" systemctl daemon-reload
"${RUN_AS_ROOT[@]}" systemctl enable "${SERVICE_NAME}.service"

echo
echo "Installed successfully."
echo "Config: ${CONFIG_DIR}/owen_config.json"
echo "Probe config: ${CONFIG_DIR}/owen_probe.json"
echo "Start service: sudo systemctl start ${SERVICE_NAME}"
echo "Status:        systemctl status ${SERVICE_NAME}"
echo "Logs:          journalctl -u ${SERVICE_NAME} -f"

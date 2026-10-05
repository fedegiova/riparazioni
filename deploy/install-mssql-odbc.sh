#!/usr/bin/env bash
#
# Install Microsoft ODBC Driver 18 for SQL Server (Ubuntu/Debian).
# Run as root:  sudo bash deploy/install-mssql-odbc.sh
#
set -euo pipefail

if ! command -v apt-get >/dev/null 2>&1; then
    echo "This script requires apt (Ubuntu/Debian)." >&2
    exit 1
fi
if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root: sudo bash $0" >&2
    exit 1
fi

CODENAME="$(. /etc/os-release && echo "${VERSION_CODENAME}")"
ARCH="$(dpkg --print-architecture)"  # amd64 | arm64
REPO_KEY="/usr/share/keyrings/microsoft-prod.gpg"

echo "==> Adding Microsoft package repository (${CODENAME}/${ARCH})"
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor -o "${REPO_KEY}"

echo "deb [arch=${ARCH} signed-by=${REPO_KEY}] \
https://packages.microsoft.com/ubuntu/${CODENAME}/prod ${CODENAME} production" \
    > /etc/apt/sources.list.d/mssql-release.list

apt-get update

echo "==> Installing msodbcsql18 and mssql-tools18"
ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18

echo "==> Adding sqlcmd to PATH"
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' > /etc/profile.d/mssql-tools18.sh

echo
echo "Done. Verify with:"
echo "  odbcinst -q            # should list 'ODBC Driver 18 for SQL Server'"
echo "  sqlcmd -S <host> -U <user> -P <password>"

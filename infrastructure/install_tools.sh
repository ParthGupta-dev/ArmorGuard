#!/usr/bin/env bash
# ArmorGuard — Security Tool Installer (Linux / macOS)
# Run from the repo root: bash scripts/install_tools.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$REPO_ROOT/tools"
ENV_FILE="$REPO_ROOT/backend/.env"
mkdir -p "$TOOLS_DIR"

set_env_var() {
    local key="$1" value="$2"
    if [ -f "$ENV_FILE" ]; then
        if grep -q "^$key=" "$ENV_FILE"; then
            sed -i.bak "s|^$key=.*|$key=$value|" "$ENV_FILE" && rm -f "$ENV_FILE.bak"
        else
            echo "$key=$value" >> "$ENV_FILE"
        fi
    fi
}

OS="$(uname -s)"
ARCH="$(uname -m)"
PD_OS="linux"; PD_ARCH="amd64"
[ "$OS" = "Darwin" ] && PD_OS="darwin"
[ "$ARCH" = "arm64" ] && PD_ARCH="arm64"

# ── nmap ──────────────────────────────────────────────────────────────────────
echo "=== nmap ==="
if command -v nmap &>/dev/null; then
    echo "nmap already installed: $(command -v nmap)"
elif [ "$OS" = "Darwin" ]; then
    brew install nmap
elif command -v apt-get &>/dev/null; then
    sudo apt-get install -y nmap
elif command -v yum &>/dev/null; then
    sudo yum install -y nmap
fi
set_env_var "NMAP_PATH" "nmap"

# ── nuclei ────────────────────────────────────────────────────────────────────
echo "=== nuclei ==="
if [ -f "$TOOLS_DIR/nuclei" ]; then
    echo "nuclei already present"
else
    URL=$(curl -s "https://api.github.com/repos/projectdiscovery/nuclei/releases/latest" \
        | grep "browser_download_url" | grep "${PD_OS}_${PD_ARCH}.zip" | head -1 | cut -d'"' -f4)
    curl -sL "$URL" -o "$TOOLS_DIR/nuclei.zip"
    unzip -q "$TOOLS_DIR/nuclei.zip" -d "$TOOLS_DIR/nuclei_tmp"
    mv "$TOOLS_DIR/nuclei_tmp/nuclei" "$TOOLS_DIR/nuclei"
    chmod +x "$TOOLS_DIR/nuclei"
    rm -rf "$TOOLS_DIR/nuclei.zip" "$TOOLS_DIR/nuclei_tmp"
    echo "nuclei installed → $TOOLS_DIR/nuclei"
fi
set_env_var "NUCLEI_PATH" "$TOOLS_DIR/nuclei"

# ── httpx (ProjectDiscovery) ──────────────────────────────────────────────────
echo "=== httpx (ProjectDiscovery) ==="
if [ -f "$TOOLS_DIR/httpx" ]; then
    echo "httpx already present"
else
    URL=$(curl -s "https://api.github.com/repos/projectdiscovery/httpx/releases/latest" \
        | grep "browser_download_url" | grep "${PD_OS}_${PD_ARCH}.zip" | head -1 | cut -d'"' -f4)
    curl -sL "$URL" -o "$TOOLS_DIR/httpx.zip"
    unzip -q "$TOOLS_DIR/httpx.zip" -d "$TOOLS_DIR/httpx_tmp"
    mv "$TOOLS_DIR/httpx_tmp/httpx" "$TOOLS_DIR/httpx"
    chmod +x "$TOOLS_DIR/httpx"
    rm -rf "$TOOLS_DIR/httpx.zip" "$TOOLS_DIR/httpx_tmp"
    echo "httpx installed → $TOOLS_DIR/httpx"
fi
set_env_var "HTTPX_PATH" "$TOOLS_DIR/httpx"

# ── nuclei templates ──────────────────────────────────────────────────────────
echo "=== nuclei templates ==="
"$TOOLS_DIR/nuclei" -update-templates 2>&1 | tail -3

echo ""
echo "All tools installed. Paths written to backend/.env"

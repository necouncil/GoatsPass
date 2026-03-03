#!/usr/bin/env bash
# ─── GoatsPass — Linux Installer ─────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/GoatsPass"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo ""
echo "  ██████╗  ██████╗  █████╗ ████████╗███████╗██████╗  █████╗ ███████╗███████╗"
echo "  ██╔════╝ ██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔════╝██╔════╝"
echo "  ██║  ███╗██║   ██║███████║   ██║   ███████╗██████╔╝███████║███████╗███████╗"
echo "  ██║   ██║██║   ██║██╔══██║   ██║   ╚════██║██╔═══╝ ██╔══██║╚════██║╚════██║"
echo "  ╚██████╔╝╚██████╔╝██║  ██║   ██║   ███████║██║     ██║  ██║███████║███████║"
echo "   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝"
echo ""
echo "  Password Manager — Linux Installer"
echo "  ────────────────────────────────────"
echo ""

# ── Check Python ──────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "  [ERROR] Python 3 not found. Install it first:"
    echo "          Arch/Manjaro: sudo pacman -S python"
    echo "          Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "          Fedora: sudo dnf install python3"
    exit 1
fi

PYTHON=$(command -v python3)
PY_VER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  [✓] Python $PY_VER found"

# ── Check pip ─────────────────────────────────────────────────────────────────
if ! $PYTHON -m pip --version &>/dev/null; then
    echo "  [!] pip not found, attempting to install..."
    if command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python-pip
    elif command -v apt &>/dev/null; then
        sudo apt install -y python3-pip
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-pip
    else
        echo "  [ERROR] Cannot install pip automatically. Install it manually."
        exit 1
    fi
fi

# ── Check tkinter ─────────────────────────────────────────────────────────────
if ! $PYTHON -c "import tkinter" &>/dev/null; then
    echo "  [!] tkinter not found, attempting to install..."
    if command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm tk
    elif command -v apt &>/dev/null; then
        sudo apt install -y python3-tk
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-tkinter
    else
        echo "  [ERROR] Install tkinter manually for your distro."
        exit 1
    fi
fi
echo "  [✓] tkinter found"

# ── Install Python packages ───────────────────────────────────────────────────
echo "  [~] Installing Python dependencies..."
PIP_FLAGS="--quiet"

# Detect if we need --break-system-packages (PEP 668)
if $PYTHON -m pip install --dry-run cryptography &>/dev/null; then
    :
else
    PIP_FLAGS="$PIP_FLAGS --break-system-packages"
fi

$PYTHON -m pip install $PIP_FLAGS cryptography argon2-cffi Pillow

echo "  [✓] Dependencies installed"

# ── Copy files ────────────────────────────────────────────────────────────────
echo "  [~] Installing GoatsPass to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/goatspass.py" "$INSTALL_DIR/goatspass.py"

if [ -f "$SCRIPT_DIR/icon.png" ]; then
    cp "$SCRIPT_DIR/icon.png" "$INSTALL_DIR/icon.png"
    echo "  [✓] Icon copied"
fi

# ── Create launcher ───────────────────────────────────────────────────────────
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/goatspass" << EOF
#!/usr/bin/env bash
exec $PYTHON "$INSTALL_DIR/goatspass.py" "\$@"
EOF
chmod +x "$BIN_DIR/goatspass"
echo "  [✓] Launcher created at $BIN_DIR/goatspass"

# ── Desktop entry ─────────────────────────────────────────────────────────────
mkdir -p "$DESKTOP_DIR"
ICON_PATH=""
[ -f "$INSTALL_DIR/icon.png" ] && ICON_PATH="$INSTALL_DIR/icon.png"

cat > "$DESKTOP_DIR/goatspass.desktop" << EOF
[Desktop Entry]
Name=GoatsPass
GenericName=Password Manager
Comment=Secure local password manager
Exec=$BIN_DIR/goatspass
Icon=$ICON_PATH
Terminal=false
Type=Application
Categories=Utility;Security;
Keywords=password;security;vault;
StartupNotify=true
EOF

if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

echo "  [✓] Desktop entry created"

# ── PATH hint ─────────────────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "  [!] Add this to your ~/.bashrc or ~/.zshrc to use 'goatspass' command:"
    echo "      export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "  ✅  GoatsPass installed successfully!"
echo "  ─────────────────────────────────────"
echo "  Run:  goatspass"
echo "        or find it in your app launcher"
echo ""

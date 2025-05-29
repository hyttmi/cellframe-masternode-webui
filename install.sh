#!/bin/bash
LC_ALL=C # Ensure ASCII locale so regex works...

EXT_IP=$(command -v curl > /dev/null && curl -4 -s ifconfig.me || echo "")
EXT_PORT=$(grep -oP '^listen_address=\K.*' /opt/cellframe-node/etc/cellframe-node.cfg | head -1 | tr -d '[]' | cut -d ':' -f 2)
PIP_PATH="/opt/cellframe-node/python/bin/pip3"
CFG_PATH="/opt/cellframe-node/etc/cellframe-node.cfg.d"
PLUGIN_PATH="/opt/cellframe-node/var/lib/plugins"
WEBUI_PATH="$PLUGIN_PATH/cellframe-masternode-webui"
CURR_PATH=$(pwd)
URL="webui"
ACCESS_TOKEN=$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 48)

install_plugin() {
    if [[ -f "$PIP_PATH" ]]; then
        echo "pip3 is available..."
        if ! [[ -x "$PIP_PATH" ]]; then
            echo "pip3 is not executable. Setting executable permissions..."
            chmod +x "$PIP_PATH" || { echo "Failed to make pip3 executable!"; exit 1; }
        fi
        echo "Installing requirements..."
        "$PIP_PATH" install -r requirements.txt > /dev/null 2>&1

        echo "Installing plugin..."
        if cp -r "$CURR_PATH"/* "$WEBUI_PATH"/; then
            echo "Plugin installed successfully!"
            echo -e "\nAccess available at:\n\n$EXT_IP:$EXT_PORT/$URL?access_token=$ACCESS_TOKEN"
            exit 0
        else
            echo "Failed to install the plugin."
            exit 1
        fi
    else
        echo "$PIP_PATH not found!"
        exit 1
    fi
}

if [[ "$1" =~ --uninstall|-u ]]; then
    [[ -f "$CFG_PATH/webui.cfg" ]] && echo "Removing configuration file..." && rm -f "$CFG_PATH/webui.cfg"
    [[ -d "$WEBUI_PATH" ]] && echo "Removing plugin directory..." && rm -rf "$WEBUI_PATH"
    echo "Plugin uninstalled successfully!"
    exit 0
fi

if [[ -f "$CFG_PATH/webui.cfg" ]]; then
    echo "Old configuration file found. Proceeding to reinstall plugin only."
    install_plugin
fi

[[ ! -d "$CFG_PATH" ]] && echo "Creating configuration directory: $CFG_PATH" && mkdir -p "$CFG_PATH"
[[ ! -d "$WEBUI_PATH" ]] && echo "Creating plugin directory: $WEBUI_PATH" && mkdir -p "$WEBUI_PATH"

echo "Writing plugin configuration to $CFG_PATH/webui.cfg"
cat > "$CFG_PATH/webui.cfg" <<EOF
[server]
enabled=true

[plugins]
enabled=true
py_load=true
py_path=../var/lib/plugins

[webui]
access_token=$ACCESS_TOKEN
EOF

read -p "Type URL which you want to register with the plugin, leave blank to use the default ($URL): " INPUT_URL
if [[ "$INPUT_URL" =~ ^[a-zA-Z0-9]+$ ]]; then
    URL=$INPUT_URL
    echo "url=$URL" >> "$CFG_PATH/webui.cfg"
else
    echo "Invalid or empty input. Using default URL: $URL"
    echo "url=$URL" >> "$CFG_PATH/webui.cfg"
fi

while true; do
    read -p "Do you want to enable automatic updates? (y/n): " INPUT_UPDATE
    if [[ "$INPUT_UPDATE" =~ ^[Yy]$ ]]; then
        echo "auto_update=true" >> "$CFG_PATH/webui.cfg"
        break
    elif [[ "$INPUT_UPDATE" =~ ^[Nn]$ ]]; then
        break
    else
        echo "Please answer with 'y' or 'n'."
    fi
done

while true; do
    read -p "Do you want to enable debug logging? (y/n): " INPUT_DEBUG_LOGGING
    if [[ "$INPUT_DEBUG_LOGGING" =~ ^[Yy]$ ]]; then
        echo "debug=true" >> "$CFG_PATH/webui.cfg"
        break
    elif [[ "$INPUT_DEBUG_LOGGING" =~ ^[Nn]$ ]]; then
        break
    else
        echo "Please answer with 'y' or 'n'."
    fi
done

install_plugin

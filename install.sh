#!/bin/bash
LC_ALL=C # Make sure we're using ASCII locale so regex works...
EXT_IP=$(dig @resolver4.opendns.com myip.opendns.com +short -4 2> /dev/null || echo "dig unavailable, can't get external IP" && EXT_IP="")
EXT_PORT=$(grep -oP '^listen_address=\K.*' /opt/cellframe-node/etc/cellframe-node.cfg | head -1 | tr -d '[]' | cut -d ':' -f 2)
PIP="pip3"
PIP_PATH="/opt/cellframe-node/python/bin/$PIP"
CFG_PATH="/opt/cellframe-node/etc/cellframe-node.cfg.d"
PLUGIN_PATH="/opt/cellframe-node/var/lib/plugins"
WEBUI_PATH="$PLUGIN_PATH/cellframe-masternode-webui"
CURR_PATH=$(pwd)

if ! [[ -d $CFG_PATH ]]; then
    echo "Creating configuration directory: $CFG_PATH"
    mkdir -p "$CFG_PATH" || { echo "Failed to create directory $CFG_PATH"; exit 1; }
fi

if ! [[ -d $WEBUI_PATH ]]; then
    echo "Creating plugin directory: $WEBUI_PATH"
    mkdir -p $WEBUI_PATH || { echo "Failed to create directory $WEBUI_PATH"; exit 1; }
fi

echo "Writing plugin configuration to $CFG_PATH/webui.cfg"
echo -e "[server]\nenabled=true\n\n[plugins]\nenabled=true\npy_load=true\npy_path=../var/lib/plugins\n\n[webui]" > "$CFG_PATH/webui.cfg" || {
    echo "Failed to write configuration file"; exit 1;
}

read -p "Type a username for WebUI user, leave blank to use default ($USERNAME): " INPUT_USERNAME
read -p "Type a password for WebUI user, leave blank to use default ($PASSWORD): " INPUT_PASSWORD
read -p "Type URL which you want to register with the plugin, leave blank to use the default ($URL):" INPUT_URL

USERNAME=${INPUT_USERNAME}
PASSWORD=${INPUT_PASSWORD}
URL=${INPUT_URL}

if  [[ ! -z $USERNAME ]] && [[ "$USERNAME" =~ ^[a-zA-Z0-9]+$ ]]; then
    echo -e "username=$USERNAME" >> "$CFG_PATH/webui.cfg" || { echo "Failed to write configuration file"; exit 1; }
else
    echo "Username $USERNAME is invalid, using default (webui)."
    USERNAME="webui"
fi

if [[ ! -z "$PASSWORD" ]] && [[ ! "$PASSWORD" =~ [[:space:]] ]]; then
    echo -e "password=$PASSWORD" >> "$CFG_PATH/webui.cfg" || { echo "Failed to write configuration file"; exit 1; }
else
    echo "Password \"$PASSWORD\" is invalid. It must not contain spaces. Using default (webui)."
    PASSWORD="webui"
fi

if [[ "$URL" =~ ^[a-zA-Z0-9]+$ ]]; then
    echo -e "uri=$URL" >> "$CFG_PATH/webui.cfg" || { echo "Failed to write configuration file"; exit 1; }
else
    echo "URL $URL is invalid. It must not contain spaces or special chars. Using default (webui)."
    URL="webui"
fi

if [[ -f $PIP_PATH ]]; then
    echo "$PIP is available..."
    if ! [[ -x $PIP_PATH ]]; then
        echo "$PIP is not executable. Setting executable permissions..."
        chmod +x "$PIP_PATH" || { echo "Failed to make $PIP executable!"; exit 1; }
    fi
    echo "Installing requirements..."
    $PIP_PATH install -r requirements.txt > /dev/null 2>&1

    echo "Installing plugin..."

    if cp -r "$CURR_PATH"/* $WEBUI_PATH/; then
        echo "Plugin installed successfully!"
    else
        echo "Failed to install the plugin."; exit 1;
    fi
else
    echo "$PIP_PATH not found!"
    exit 1
fi

echo -e "\n\nYou may login after node restart with http://$EXT_IP:$EXT_PORT/$URL"
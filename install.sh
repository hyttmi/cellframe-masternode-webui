#!/bin/bash
LC_ALL=C # Make sure we're using ASCII locale so regex works...
EXT_IP=$(command -v curl > /dev/null && curl -4 -s ifconfig.me || echo "")
EXT_PORT=$(grep -oP '^listen_address=\K.*' /opt/cellframe-node/etc/cellframe-node.cfg | head -1 | tr -d '[]' | cut -d ':' -f 2)
PIP="pip3"
PIP_PATH="/opt/cellframe-node/python/bin/$PIP"
CFG_PATH="/opt/cellframe-node/etc/cellframe-node.cfg.d"
PLUGIN_PATH="/opt/cellframe-node/var/lib/plugins"
WEBUI_PATH="$PLUGIN_PATH/cellframe-masternode-webui"
CURR_PATH=$(pwd)
USERNAME="webui"
PASSWORD="webui"
URL="webui"

generate_random_password() {
    tr -dc 'A-Za-z0-9!@#$%&-+=' < /dev/urandom | head -c 16
}

install_plugin() {
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
            echo "Plugin installed successfully!"; exit 0;
        else
            echo "Failed to install the plugin."; exit 1;
        fi
        else
            echo "$PIP_PATH not found!"
            exit 1
        fi
}

if [[ "$1" =~ --uninstall|-u ]]; then
    if [[ -f "$CFG_PATH/webui.cfg" ]]; then
        echo "Removing configuration file..."
        rm -f "$CFG_PATH/webui.cfg" || { echo "Failed to remove configuration file!"; exit 1; }
    fi
    if [[ -d "$WEBUI_PATH" ]]; then
        echo "Removing plugin directory..."
        rm -rf "$WEBUI_PATH" || { echo "Failed to remove plugin directory!"; exit 1; }
    fi
    echo "Plugin uninstalled successfully!"; exit 0;
fi

if [[ -f "$CFG_PATH/webui.cfg" ]]; then
    echo "Old configuration file found, proceeding to install only!"
    install_plugin
fi

if ! [[ -d $CFG_PATH ]]; then
    echo "Creating configuration directory: $CFG_PATH"
    mkdir -p "$CFG_PATH" || { echo "Failed to create directory $CFG_PATH"; exit 1; }
fi

if ! [[ -d $WEBUI_PATH ]]; then
    echo "Creating plugin directory: $WEBUI_PATH"
    mkdir -p $WEBUI_PATH || { echo "Failed to create directory $WEBUI_PATH"; exit 1; }
fi

echo "Writing plugin configuration to $CFG_PATH/webui.cfg"
echo -e "[server]\nenabled=true\n\n[plugins]\nenabled=true\npy_load=true\npy_path=../var/lib/plugins" > "$CFG_PATH/webui.cfg" || {
    echo "Failed to write configuration file"; exit 1;
}

read -p "Type a username for WebUI user, leave blank to use default ($USERNAME): " INPUT_USERNAME

if [[ -n "$INPUT_USERNAME" ]] && [[ "$INPUT_USERNAME" =~ ^[a-zA-Z0-9]+$ ]]; then
    USERNAME=$INPUT_USERNAME
    echo -e "\n[webui]\nusername=$USERNAME" >> "$CFG_PATH/webui.cfg" || { echo "Failed to write configuration file"; exit 1; }
else
    echo "Username $INPUT_USERNAME is invalid, using default ($USERNAME)."
    echo -e "\n[webui]\nusername=$USERNAME" >> "$CFG_PATH/webui.cfg" || { echo "Failed to write configuration file"; exit 1; }
fi

read -p "Type a password for WebUI user, leave blank to generate a random password: " INPUT_PASSWORD

if [[ -n "$INPUT_PASSWORD" ]] && [[ "$INPUT_PASSWORD" =~ ^[a-zA-Z0-9\_\!\@\$\%\^\&\*\(\)\-\+\=]+$ ]]; then
    PASSWORD=$INPUT_PASSWORD
else
    PASSWORD=$(generate_random_password)
    echo "Generated random password: $PASSWORD"
fi

echo -e "password=$PASSWORD" >> "$CFG_PATH/webui.cfg" || { echo "Failed to write configuration file"; exit 1; }


read -p "Type URL which you want to register with the plugin, leave blank to use the default ($URL):" INPUT_URL

if [[ "$INPUT_URL" =~ ^[a-zA-Z0-9]+$ ]]; then
    URL=$INPUT_URL
    echo -e "uri=$URL" >> "$CFG_PATH/webui.cfg" || { echo "Failed to write configuration file"; exit 1; }
else
    echo "URL $INPUT_URL is invalid. It must not contain spaces or special chars. Using default (webui)."
    echo -e "uri=$URL" >> "$CFG_PATH/webui.cfg" || { echo "Failed to write configuration file"; exit 1; }
fi

read -p "Do you want to enable automatic updates? (y/n): " INPUT_UPDATE

if [[ "$INPUT_UPDATE" =~ ^[Yy]$ ]]; then
    echo -e "auto_update=true" >> "$CFG_PATH/webui.cfg" || { echo "Failed to write configuration file"; exit 1; }
fi

install_plugin
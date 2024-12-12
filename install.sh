#!/bin/bash
PIP="pip3"
PIP_PATH="/opt/cellframe-node/python/bin/$PIP"
CFG_PATH="/opt/cellframe-node/etc/cellframe-node.cfg.d"
PLUGIN_PATH="/opt/cellframe-node/var/lib/plugins/"
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

echo "Writing plugin configuration to $CFG_PATH/plugins.cfg"
echo -e "[server]\nenabled=true\n\n[plugins]\nenabled=true\npy_load=true\npy_path=../var/lib/plugins" > "$CFG_PATH/webui.cfg" || {
    echo "Failed to write configuration file"; exit 1;
}

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
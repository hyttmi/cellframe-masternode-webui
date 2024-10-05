# Cellframe masternode WebUI
![image](https://github.com/user-attachments/assets/6c311087-77bd-40aa-99fc-a42ca284a3f1)


With this plugin, it's easy to check your node autocollect stats and some other things too. 100% themeable!

## Configuration

**NOTICE: Email feature supports only GMail for now. And for using it, you MUST HAVE 2-factor authentication enabled and you HAVE TO create an app password from this link:  https://myaccount.google.com/apppasswords**

Configuration of the plugin is done by editing `cellframe-node.cfg` file in `/opt/cellframe-node/etc/cellframe-node.cfg`. You just need to add new section `[webui]` to the end of the file and below that, add the settings which you want to change:

- `username=john` - Sets http authentication as user john. **MANDATORY**
- `password=p455w0rd` - Sets password to p455w0rd. **MANDATORY**  
- `template=something` - Change template to something. If not set, default template will be used (cards).
- `uri=something` - Change plugin URI. Defaults to `webui`
- `header_text=sometext` - Show `sometext` as a website header **WITHOUT SPACES**
- `email_stats=true|false` - Allow sending scheduled email statistics
- `email_time=17:39` - Set time when you want to send the statistics **24h format (HH:MM)**
- `gmail_app_password=asdf asdf asdf asdf` - GMail app password
- `gmail_user=somebody@gmail.com` - Your GMail username
- `email_recipients=somebody@gmail.com|[somebody@gmail.com, another@aol.com]` - Recipient(s) for the email
- `telegram_stats=true|false` - Enable timed Telegram messages
- `telegram_api_key=something` - Your Telegram Bot API token
- `telegram_chat_id=something` - Your Telegram chat id
- `telegram_stats_time=23:59` - Time to send the message **24h format (HH:MM)**

## Installation

1. Enable Python plugins in `cellframe-node.cfg` so it looks on the bottom something like this:
```
# Plugins
[plugins]
enabled=true
# Load Python-based plugins
py_load=true
py_path=/opt/cellframe-node/var/lib/plugins

```
2. Place the `webui` directory to `/opt/cellframe-node/var/lib/plugins/` (If it doesn't exist, create it).
3. Go to `/opt/cellframe-node/python/bin` and make sure pip/pip3 is executable `(chmod +x pip pip3)`
4. Go back to `/opt/cellframe-node/var/lib/plugins/webui` and install required packages with `/opt/cellframe-node/python/bin/pip3 install -r requirements.txt` **AS ROOT**
5. Restart your node and access the WebUI with your browser (`http://<your_node_ip>:<your_node_port>/<uri>` where `<uri>` by default is webui).

## Updating

1. Overwrite the old files in `/opt/cellframe-node/var/lib/plugins/webui`
2. Go to `/opt/cellframe-node/var/lib/plugins/webui` and install required packages with `/opt/cellframe-node/python/bin/pip3 install -r requirements.txt` **AS ROOT**
3. Restart your node and access the WebUI with your browser (`http://<your_node_ip>:<your_node_port>/<uri>` where `<uri>` by default is webui).

## Templating

All `.html` files in `templates/cards` are the default templates for Telegram, WebUI and email.

This plugin renders system and node information to a web interface using Jinja templates. It collects data such as node status, network statistics, and system uptime, and formats it into HTML.

### Available Variables

Here are the variables that are passed to the Jinja templates:

- `plugin_name`: The name of the plugin.
- `update_available`: Checks if there's update available for plugin
- `current_version`: Shows current version of this plugin
- `latest_version`: Returns the latest version of this plugin
- `title`: Return plugin name
- `hostname`: Returns your systems hostname
- `external_ip`: Returns external IP address
- `system_uptime`: Returns your system uptime
- `node_uptime`: Returns Cellframe node uptime
- `node_version`: Returns the currently installed version of Cellframe node
- `latest_node_version`: Returns the latest version of Cellframe node
- `cpu_utilization`: Returns the current CPU utilization of Cellframe node
- `memory_utilization`: Returns the current memory utilization of Cellframe node
- `network_data`: A list of dictionaries containing network information.
  - `name`: The name of the network
  - `state`: The current state of the network (online/offline)
  - `target_state`: The target state of the network
  - `address`: The network address
  - `first_signed_blocks`: The number of first signed blocks
  - `all_signed_blocks`: The total number of signed blocks
  - `all_blocks`: The total number of blocks
  - `signed_blocks_today`: The number of blocks signed today
  - `signed_blocks_last_7_days`: A dictionary of blocks signed in the last 7 days
  - `autocollect_status`: The status of reward autocollection
  - `rewards`: The total rewards currenly uncollected
  - `fee_wallet_tokens`: A list of token balances in the network's fee wallet






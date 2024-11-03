# Cellframe masternode WebUI
![image](https://github.com/user-attachments/assets/f0520e69-a6ae-4efc-8ec1-56a1a967031c)

![image](https://github.com/user-attachments/assets/ae551135-1037-4f43-9104-9bb300332463)

This plugin offers an easy and efficient way to monitor your node's autocollect statistics and manage other important features. Whether you're tracking performance or keeping an eye on your node's signing activity, this tool provides a user-friendly interface to help you stay informed. Plus, it's fully customizable and 100% themeable, allowing you to tailor the look and feel to match your preferences or existing setup.

## Configuration

Configuration of the plugin is done by editing `cellframe-node.cfg` file in `/opt/cellframe-node/etc/cellframe-node.cfg`. You just need to add new section `[webui]` to the end of the file and below that, add the settings which you want to change:

- `accent_color=FFFFFF` - Use hex code color as the accent color (without #).
- `api_token=your_own_api_token`- Used in accessing plain JSON data (You can generate your own or use a service like https://it-tools.tech/token-generator).
- `auth_bypass=true|false` Disables HTTP authentication. Useful if you're planning to for example use the plugin behind reverse proxy. Default false.
- `cache_blocks_interval=10` - Time (in minutes) between blocks cache renew.
- `cache_rewards_interval=10` - Time (in minutes) between rewards cache renew. **DON'T USE VALUE BELOW 10, IT USES QUITE A LOT OF CPU**
- `email_recipients=somebody@gmail.com|[somebody@gmail.com, another@aol.com]` - Recipient(s) for the email.
- `email_stats=true|false` - Allow sending scheduled email statistics.
- `email_time=23:59` - Set time when you want to send the statistics. **24h format (HH:MM)**
- `email_use_ssl=true|false` - Use SSL for mail delivery.
- `email_use_tls=true|false` - Use TLS for mail delivery.
- `header_text=sometext` - Show `sometext` as a website header **WITHOUT SPACES**
- `password=p455w0rd` - Sets password to p455w0rd. **MANDATORY UNLESS `auth_bypass` SET TO TRUE**
- `rate_limit_interval=15` Sets rate limit interval to 15 seconds.
- `rate_limit=true|false` - If set, rate limit per request will be set to 15 seconds. Default false.
- `smtp_password=<your_smtp_password>` - SMTP password for mail delivery.
- `smtp_port=465` - SMTP port to use for mail delivery.
- `smtp_server=your.smtp.server.com` - SMTP server to use for mail delivery.
- `smtp_user=<your_email_user>` - SMTP user for mail delivery.
- `telegram_api_key=something` - Your Telegram Bot API token.
- `telegram_chat_id=something` - Your Telegram chat id.
- `telegram_stats_time=23:59` - Time to send the message. **24h format (HH:MM)**
- `telegram_stats=true|false` - Enable timed Telegram messages.
- `template=something` - Change template to something. If not set, default template will be used (cards).
- `uri=something` - Change plugin URI. Defaults to `webui`.
- `username=john` - Sets http authentication as user john. **MANDATORY UNLESS `auth_bypass` SET TO TRUE**

### Using GMail with email stats

1. Enable 2FA!
2. Create an app password https://myaccount.google.com/apppasswords
3. Use the following configuration:

```
smtp_server=smtp.gmail.com
smtp_port=587
smtp_password=<your_app_password>
smtp_user=<your_gmail_user>
email_use_tls=true
```

## Installation

You can get the latest release from [releases page](https://github.com/hyttmi/cellframe-masternode-webui/releases) or by cloning this repo.

1. Enable Python plugins in `cellframe-node.cfg` so it looks on the end of the file something like this:
```
# Plugins
[plugins]
enabled=true
# Load Python-based plugins
py_load=true
py_path=../var/lib/plugins

```
2. Place the `cellframe-masternode-webui` directory to `/opt/cellframe-node/var/lib/plugins/` (If it doesn't exist, create it).
3. Go to `/opt/cellframe-node/python/bin` and make sure pip/pip3 is executable `(chmod +x pip pip3)`
4. Go back to `/opt/cellframe-node/var/lib/plugins/cellframe-masternode-webui` and install required packages with `/opt/cellframe-node/python/bin/pip3 install -r requirements.txt` **AS ROOT**
5. Restart your node and access the WebUI with your browser (`http://<your_node_ip>:<your_node_port>/<url>` where `<url>` by default is webui).

## Updating

1. Overwrite the old files in `/opt/cellframe-node/var/lib/plugins/webui`
2. Go to `/opt/cellframe-node/var/lib/plugins/webui` and install required packages with `/opt/cellframe-node/python/bin/pip3 install -r requirements.txt` **AS ROOT**
3. Restart your node and access the WebUI with your browser (`http://<your_node_ip>:<your_node_port>/<url>` where `<url>` by default is webui).

## Templating

All `.html` files in `templates/cards` are the default templates for Telegram, WebUI and email.

This plugin renders system and node information to a web interface using Jinja templates. It collects data such as node status, network statistics, and system uptime, and formats it into HTML.

### Available Variables

Here are the variables that are passed to the Jinja templates:

- `plugin_name`: The name of the plugin.
- `plugin_update_available`: Checks if there's update available for plugin
- `current_plugin_version`: Shows current version of this plugin
- `latest_plugin_version`: Returns the latest version of this plugin
- `plugin_title`: Return plugin name
- `hostname`: Returns your systems hostname
- `node_active_threads`: Returns active threads spawned by Cellframe node
- `system_uptime`: Returns your system uptime in seconds
- `node_uptime`: Returns Cellframe node uptime in seconds
- `node_version`: Returns the currently installed version of Cellframe node
- `latest_node_version`: Returns the latest version of Cellframe node **NOTE: THIS VALUE IS CACHED FOR 2 HOUR AFTER IT'S FETCHED**
- `node_cpu_utilization`: Returns the current CPU utilization of Cellframe node
- `node_memory_utilization`: Returns the current memory utilization of Cellframe node
- `website_accent_color`: Returns the accent color from cellframe-node.cfg
- `networks`: A dictionary containing network information.
  - `name`: The name of the network
  - `state`: The current state of the network
  - `target_state`: Target state of the network
  - `address`: The network address
  - `first_signed_blocks`: The number of first signed blocks
  - `all_signed_blocks`: The number of all signed blocks
  - `all_blocks`: The number of blocks in main chain
  - `signed_blocks_today`: The number of blocks signed today
  - `all_signed_blocks_dict`: A dictionary of all signed blocks (day, amount)
  - `autocollect_status`: The status of reward autocollection
  - `autocollect_rewards`: The total autocollect rewards currently uncollected
  - `fee_wallet_tokens`: A dict of token balances in the network's fee wallet
  - `rewards`: A dictionary of rewards from last 7 days
  - `token_price`: Tries to fetch and return the latest token price from CMC **NOTE: THIS VALUE IS CACHED FOR 1 HOUR AFTER IT'S FETCHED**

## Accessing data as JSON
By default, this plugin has support for fetching all the important data from your node as JSON if you have `api_token` set in settings. Here's a sample code for fetching the data with Python:

```
import requests, json

def fetch_node_info(url, api_token):
    headers = {
        "API_TOKEN": api_token
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            json_data = response.json()
            return json_data
        else:
            print(f"Error with a status code {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

url = "http://<your_node_ip:8079/webui?as_json"
api_token = "<your_custom_api_token"

data = fetch_node_info(url, api_token)

if data is not None:
    print(json.dumps(data, indent=4))
```

And with on terminal with `curl` piping to `jq`:
```
curl -s "http://<your_node_ext_ip>:8079/webui?as_json" -H "API_TOKEN: <your_api_token>" | jq .net_info.Backbone.signed_blocks_today -> Returns the amount of signed blocks today
```

```
curl -s "http://<your_node_ext_ip>:8079/webui?as_json" -H "API_TOKEN: <your_api_token>" | jq .node_uptime -> Returns node uptime in (days), hours, minutes, seconds
```

```
curl -s "http://<your_node_ext_ip>:8079/webui?as_json" -H "API_TOKEN: <your_api_token>" | jq -> Returns all data
```
```
curl -s "http://<your_node_ext_ip>:8079/webui?as_json" -H "API_TOKEN: <your_api_token>" | jq '.networks.Backbone.rewards | add' -> Calculates all your earned rewards in Backbone network
```






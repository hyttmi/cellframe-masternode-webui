# Cellframe masternode WebUI
![image](https://github.com/user-attachments/assets/f0520e69-a6ae-4efc-8ec1-56a1a967031c)

![image](https://github.com/user-attachments/assets/ae551135-1037-4f43-9104-9bb300332463)

With this plugin, it's easy to check your node autocollect stats and some other things too. 100% themeable!

## Configuration

**NOTICE: Email feature supports only GMail for now. And for using it, you MUST HAVE 2-factor authentication enabled and you HAVE TO create an app password from this link: https://myaccount.google.com/apppasswords**

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
- `cache_rewards=true|false`- Cache rewards to a text file **MANDATORY FOR SHOWING REWARDS FROM LAST 7 DAYS**
- `cache_rewards_time=10` - Time (in minutes) between rewards cache renew, **DON'T USE VALUE BELOW 10, IT USES QUITE A LOT OF CPU**
- `accent_color=FFFFFF` - Use hex code color as the accent color (without #)
- `api_token=your_own_api_token`- Used in accessing plain JSON data (You can generate your own or use a service like https://it-tools.tech/token-generator)
- `rate_limit=true|false` - If set, rate limit per request will be set to 15 seconds

## Installation

You can get the latest release from [releases page](https://github.com/hyttmi/cellframe-masternode-webui/releases) or by cloning this repo.

1. Enable Python plugins in `cellframe-node.cfg` so it looks on the end of the file something like this:
```
# Plugins
[plugins]
enabled=true
# Load Python-based plugins
py_load=true
py_path=/opt/cellframe-node/var/lib/plugins

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
- `accent_color`: Returns the accent color from cellframe-node.cfg
- `network_info`: A list of dictionaries containing network information.
  - `name`: The name of the network
  - `state`: The current state of the network (online/offline)
  - `target_state`: The target state of the network
  - `address`: The network address
  - `first_signed_blocks`: The number of first signed blocks
  - `all_signed_blocks`: The number of all signed blocks
  - `all_blocks`: The number of blocks
  - `signed_blocks_today`: The number of blocks signed today
  - `signed_blocks_all`: A dictionary of all signed blocks (day, amount)
  - `autocollect_status`: The status of reward autocollection
  - `autocollect_rewards`: The total rewards currently uncollected
  - `fee_wallet_tokens`: A list of token balances in the network's fee wallet
  - `rewards`: A dict of rewards from last 7 days

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
curl "http://<your_node_ext_ip>:8079/webui?as_json" -H "API_TOKEN: <your_api_token>" | jq .net_info.Backbone.signed_blocks_today -> Returns the amount of signed blocks today
```

```
curl "http://<your_node_ext_ip>:8079/webui?as_json" -H "API_TOKEN: <your_api_token>" | jq .node_uptime -> Returns node uptime in (days), hours, minutes, seconds
```

```
curl "http://<your_node_ext_ip>:8079/webui?as_json" -H "API_TOKEN: <your_api_token>" | jq -> Returns all data
```





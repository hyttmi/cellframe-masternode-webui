# Cellframe masternode WebUI
![image](https://github.com/user-attachments/assets/f0520e69-a6ae-4efc-8ec1-56a1a967031c)

![image](https://github.com/user-attachments/assets/ae551135-1037-4f43-9104-9bb300332463)

This plugin offers an easy and efficient way to monitor your node's autocollect statistics and manage other important features. Whether you're tracking performance or keeping an eye on your node's signing activity, this tool provides a user-friendly interface to help you stay informed. Plus, it's fully customizable and 100% themeable, allowing you to tailor the look and feel to match your preferences.

## Installation

You can get the latest release from [releases page](https://github.com/hyttmi/cellframe-masternode-webui/releases) or by cloning this repo.

1. Set provided `install.sh` script executable with `chmod +x install.sh`.
2. Run the script as root with `sudo ./install.sh`.
3. Before restarting your node, please read **carefully** how to [configure the plugin](#configuration).
4. Restart your node and access the WebUI with your browser (`http://<your_node_ip>:<your_node_port>/<url>` where `<url>` by default is webui).

## Configuration

Configuration of the plugin is done by editing `cellframe-node.cfg` file in `/opt/cellframe-node/etc/cellframe-node.cfg`. You just need to add new section `[webui]` to the end of the file and below that, add the settings which you want to change:

- `api_token=your_own_api_token`- Used in accessing plain JSON data (You can generate your own or use a service like https://it-tools.tech/token-generator).
- `auth_bypass=true|false` Disables HTTP authentication. Useful if you're planning to for example use the plugin behind reverse proxy. Default false.
- `auto_update=true|false` Updates plugin files and restarts the node after update.
- `cache_blocks_interval=10` - Time (in minutes) between blocks cache renew.
- `cache_rewards_interval=10` - Time (in minutes) between rewards cache renew.
- `debug=true|false` - Print debugging data to `webui.log`, useful when you're having issues with the plugin.
- `email_recipients=somebody@gmail.com|[somebody@gmail.com, another@aol.com]` - Recipient(s) for the email.
- `email_stats=true|false` - Allow sending scheduled email statistics.
- `email_time=23:59` - Set time when you want to send the statistics. **24h format (HH:MM)**
- `email_use_ssl=true|false` - Use SSL for mail delivery.
- `email_use_tls=true|false` - Use TLS for mail delivery.
- `password=p455w0rd` - Sets password to p455w0rd. Default: `webui`
- `scheduler_delay_on_startup` - Sets delay for functions which are passed to scheduler and launched directly on startup. Default value is 60 seconds
- `smtp_password=<your_smtp_password>` - SMTP password for mail delivery.
- `smtp_port=465` - SMTP port to use for mail delivery.
- `smtp_server=your.smtp.server.com` - SMTP server to use for mail delivery.
- `smtp_user=<your_email_user>` - SMTP user for mail delivery.
- `telegram_api_key=something` - Your Telegram Bot API token.
- `telegram_chat_id=something` - Your Telegram chat id.
- `telegram_stats_time=23:59` - Time to send the message. **24h format (HH:MM)**
- `telegram_stats=true|false` - Enable timed Telegram messages.
- `template=something` - Change template to something. If not set, default template will be used (cards). Oldskool theme is also available by default.
- `uri=something` - Change plugin URI. Defaults to `webui`.
- `username=john` - Sets http authentication as user john. Default: `webui`

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

## Updating
1. Overwrite the old files in `/opt/cellframe-node/var/lib/plugins/webui`
2. Go to `/opt/cellframe-node/var/lib/plugins/webui` and install required packages with `/opt/cellframe-node/python/bin/pip3 install -r requirements.txt` **AS ROOT**
3. Restart your node and access the WebUI with your browser (`http://<your_node_ip>:<your_node_port>/<url>` where `<url>` by default is webui).

## Templating

`email.html` and `telegram.html` are located in the templates directory.

All theme specific `.html` files are located in `templates/<theme_specific_subfolder>`.

### Available Variables

Here are the variables that are passed to the Jinja templates:

- `general_info.plugin_name`: The name of the plugin.
- `general_info.plugin_update_available`: Checks if there's update available for plugin
- `general_info.current_plugin_version`: Shows current version of this plugin
- `general_info.latest_plugin_version`: Returns the latest version of this plugin
- `general_info.plugin_title`: Return plugin name
- `general_info.hostname`: Returns your system hostname
- `general_info.system_uptime`: Returns your system uptime in seconds
- `general_info.node_uptime`: Returns Cellframe node uptime in seconds
- `general_info.node_version`: Returns the currently installed version of Cellframe node
- `general_info.latest_node_version`: Returns the latest version of Cellframe node
- `general_info.node_cpu_usage`: Returns the current CPU utilization of Cellframe node
- `general_info.node_memory_usage`: Returns the current memory utilization of Cellframe node
- `general_info.external_ip`: Returns external IP address
- `network_info`: Returns a dict containing data specific per network
  - `network_info.address`: The network address
  - `network_info.all_blocks`: The number of blocks in main chain
  - `network_info.all_rewards`: Total sum of received rewards
  - `network_info.all_signed_blocks_dict`: A dictionary of all signed blocks (day, amount)
  - `network_info.all_signed_blocks`: The number of all signed blocks
  - `network_info.autocollect_rewards`: The total autocollect rewards currently uncollected
  - `network_info.autocollect_status`: The status of reward autocollection
  - `network_info.fee_wallet_tokens`: A dict of token balances in the network's fee wallet
  - `network_info.first_signed_blocks`: The number of first signed blocks
  - `network_info.general_node_info`: Returns the output from `cellframe-node-cli node dump -<network>`
  - `network_info.node_data`: Returns a dict containing information about your node (like private key hash, stake transaction hash etc.)
  - `network_info.rewards`: A dictionary of all rewards
  - `network_info.signed_blocks_today`: The number of blocks signed today
  - `network_info.state`: The current state of the node in network
  - `network_info.target_state`: Target state for the network
  - `network_info.token_price`: Tries to fetch and return the latest token price from CMC

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
curl -s "http://<your_node_ext_ip>:8079/webui?as_json" -H "API_TOKEN: <your_api_token>" | jq .node_uptime -> Returns node uptime in seconds
```

```
curl -s "http://<your_node_ext_ip>:8079/webui?as_json" -H "API_TOKEN: <your_api_token>" | jq -> Returns all data
```
```
curl -s "http://<your_node_ext_ip>:8079/webui?as_json" -H "API_TOKEN: <your_api_token>" | jq '.networks.Backbone.rewards | add' -> Calculates all your earned rewards in Backbone network
```






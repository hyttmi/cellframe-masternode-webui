# Cellframe masternode WebUI
![image](https://github.com/user-attachments/assets/df07a2fd-fb9c-4dda-be3a-a7711e419867)

This plugin offers an easy and efficient way to monitor your node's autocollect statistics and manage other important features. Whether you're tracking performance or keeping an eye on your node's signing activity, this tool provides a user-friendly interface to help you stay informed. Plus, it's fully customizable and 100% themeable, allowing you to tailor the look and feel to match your preferences.

## Installation

### Easy way
```shell
curl -s https://api.github.com/repos/hyttmi/cellframe-masternode-webui/releases/latest | \
grep "tarball_url" | \
cut -d ":" -f 2,3 | \
tr -d '",' | \
xargs curl -L -o cellframe-masternode-webui.tar.gz \
&& mkdir -p webui \
&& tar -xvf cellframe-masternode-webui.tar.gz --strip-components=1 -C webui \
&& cd webui \
&& sudo ./install.sh
```
And answer the questions.

### Manual way

You can get the latest release from [releases page](https://github.com/hyttmi/cellframe-masternode-webui/releases) or by cloning this repo.

1. Set provided `install.sh` script executable with `chmod +x install.sh`.
2. Run the script as root with `sudo ./install.sh`.
3. Before restarting your node, please read **carefully** how to [configure the plugin](#configuration). Please note the configuration file which is reported when running the installer!
4. Restart your node and access the WebUI with your browser (`http://<your_node_ip>:<your_node_port>/<url>` where `<url>` by default is webui).

## Updating

1. Download latest version from [releases page](https://github.com/hyttmi/cellframe-masternode-webui/releases) or by cloning this repo.
   - Extract the file if you have downloaded an archive.
2. Open the dir and run `install.sh` as root.

### Easy way
Set `auto_update=true` to configuration file, restart node and wait until plugin updates itself and restarts your node.

### Manual way
Download the latest zip, execute `install.sh` as root and restart node.

## Removing
Run `install.sh -u` or `install.sh --uninstall` as root.

## Configuration

1. Create a configuration file in `/opt/cellframe-node/etc/cellframe-node.cfg.d/` directory. The file name should be `webui.cfg`.
2. Add the configuration to the file. The configuration file should be in the following format:
```
[webui]
configuration_option=value
```
3. Restart the node.

### Configuration options

- `access_token=your_own_access_token`- Used in accessing WebUI or fetching JSON data. (You can generate your own or use a service like https://it-tools.tech/token-generator).
- `auth_bypass=true|false` Disables HTTP authentication. Useful if you're planning to for example use the plugin behind reverse proxy. Default false.
- `auto_update=true|false` Updates plugin files and restarts the node after update.
- `cache_age_limit=2` - Time in hours to inform user if blocks cache is older than this value. Default 2 hours.
- `cache_blocks_interval=10` - Time (in minutes) between blocks cache renew.
- `cache_rewards_interval=10` - Time (in minutes) between rewards cache renew.
- `cli_disallowed_commands=command1|[command1, command2, command3]`- Disallow certain commands to be executed via CLI. Default is None, accepts one string or a list of strings.
- `debug=true|false` - Print debugging data to `webui.log`, useful when you're having issues with the plugin.
- `download_prereleases=true|false` - Automatic updater downloads also pre-release versions of plugin. Default false.
- `email_recipients=somebody@gmail.com|[somebody@gmail.com, another@aol.com]` - Recipient(s) for the email.
- `email_stats=true|false` - Allow sending scheduled email statistics.
- `email_time=23:59` - Set time when you want to send the statistics. Default time is 23:00 **24h format (HH:MM)**
- `email_use_ssl=true|false` - Use SSL for mail delivery.
- `email_use_tls=true|false` - Use TLS for mail delivery.
- `heartbeat_auto_restart=true|false` - Automatically restart node if heartbeat fails. Default true.
- `heartbeat_block_age=12`- Sets maximum age of last signed block to 12 hours and if older, notifies user.
- `heartbeat_interval=30` - Sets heartbeat check interval to 30 minutes.
- `heartbeat_notification_amount=5` - Sets number of notifications to be sent if heartbeat fails.
- `hide_icon=true|false` - Hide icon from the top of the page, default true.
- `node_alias="Name` - Name of the node as alias. Default is CFNode. **NO SPACES**
- `password=p455w0rd` - Sets password to p455w0rd. Default: `webui`
- `scheduler_delay_on_startup` - Sets delay for functions which are passed to scheduler and launched directly on startup. Default value is 60 seconds
- `smtp_password=<your_smtp_password>` - SMTP password for mail delivery.
- `smtp_port=465` - SMTP port to use for mail delivery.
- `smtp_server=your.smtp.server.com` - SMTP server to use for mail delivery.
- `smtp_user=<your_email_user>` - SMTP user for mail delivery.
- `stats_interval=60` - Sends statistics via notifiers every 60 minutes. Disable by setting value to 0. Default value is 0 (disabled)
- `telegram_api_key=something` - Your Telegram Bot API token.
- `telegram_bot_key=something|[something, something, something]` - Your Telegram bot UUID from https://t.me/Cellframe_Masternode_WebUI_Bot or multiple UUIDs as list.
- `telegram_chat_id=something` - Your Telegram chat id.
- `telegram_stats_time=23:59` - Time to send the message. Default time is 23:00 **24h format (HH:MM)**
- `telegram_stats=true|false` - Enable Telegram messaging support.
- `template=something` - Change template to something. If not set, default template will be used (cards).
- `url=something` - Change plugin URL. Defaults to `webui`.
- `username=john` - Sets http authentication as user john. Default: `webui`
- `websocket_server_port` - Sets WebSocket server port, default is `40000`

## Templating
Since version 3.18, it's possible to create custom templates for `email.html` and `telegram.html`. The files should be placed in `custom_templates` directory.

Default `email.html` and `telegram.html` templates are placed in `templates` directory and you can use them as the base for your own templates.

All theme specific files are located in `templates/<theme_specific_subfolder>`.

### Available Variables

Here are the variables that are passed to the Jinja templates:

- `general_info.plugin_name`: The name of the plugin.
- `general_info.current_plugin_version`: Shows current version of this plugin
- `general_info.current_config`: Displays the current configuration of the plugin.
- `general_info.latest_plugin_version`: Returns the latest version of this plugin
- `general_info.plugin_title`: Return plugin name
- `general_info.hostname`: Returns your system hostname, this value is cached and will refresh only after restart of node
- `general_info.system_uptime`: Returns your system uptime in seconds
- `general_info.node_uptime`: Returns Cellframe node uptime in seconds
- `general_info.node_version`: Returns the currently installed version of Cellframe node.
- `general_info.latest_node_version`: Returns the latest version of Cellframe node
- `general_info.node_cpu_usage`: Returns the current CPU utilization of Cellframe node
- `general_info.node_memory_usage`: Returns the current memory utilization of Cellframe node
- `general_info.external_ip`: Returns external IP address
- `network_info`: Returns a dict containing data specific per network
    - `network_info.address`: The network address
    - `network_info.all_blocks`: The number of blocks in the main chain
    - `network_info.all_signed_blocks_dict`: A dictionary of all signed blocks (per day, amount)
    - `network_info.all_signed_blocks`: The total number of all signed blocks
    - `network_info.autocollect_status`: The status of reward autocollection
    - `network_info.blocks_today`: The number of blocks signed today in this network
    - `network_info.chain_size`: The chain size (total storage used) of the main chain
    - `network_info.current_block_reward`: The reward value for signing the current block
    - `network_info.first_signed_blocks_dict`: A dictionary of first signed blocks (per day, amount)
    - `network_info.first_signed_blocks`: The number of first signed blocks
    - `network_info.first_signed_blocks_today`: The number of first signed blocks today
    - `network_info.node_data`: A dictionary containing information about all nodes in the network
    - `network_info.rewards`: A dictionary of all received rewards
    - `network_info.rewards_all_time_average`: The average amount of rewards all time
    - `network_info.rewards_today`: The sum of rewards received today
    - `network_info.sovereign_rewards`: A dictionary of sovereign rewards
    - `network_info.sovereign_rewards_all_time_average`: The average amount of sovereign rewards all time
    - `network_info.sovereign_rewards_today`: The sum of sovereign rewards received today
    - `network_info.signed_blocks_today`: The number of blocks signed today
    - `network_info.sum_rewards`: The total sum of all rewards received
    - `network_info.sum_sovereign_rewards`: The total sum of all sovereign rewards received
    - `network_info.token_price`: The latest token price from CMC or alternative source

## Accessing data as JSON
By default, this plugin has support for fetching all the important data from your node as JSON if you have `access_token` set in settings. Here's a sample code for fetching the data with Python:

```
import requests, json, gzip

def fetch_node_info(url, access_token):
    headers = {
        "ACCESS_TOKEN": access_token
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            decompressed = gzip.decompress(response.content)
            return json.loads(decompressed.decode("utf-8"))
        print(f"Error with a status code {response.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False

url = "http://<your_node_ip:8079/webui?as_json"
access_token = "<your_custom_access_token"

data = fetch_node_info(url, access_token)

if data:
    print(json.dumps(data, indent=4))
```

And with on terminal with `curl` piping to `jq`:
```
curl --compressed -s "http://<your_node_ext_ip>:8079/webui?as_json" -H "ACCESS_TOKEN: <your_access_token>" --output - | gunzip | jq .net_info.Backbone.signed_blocks_today -> Returns the amount of signed blocks today
```

```
curl --compressed -s "http://<your_node_ext_ip>:8079/webui?as_json" -H "ACCESS_TOKEN: <your_access_token>" --output - | gunzip | jq .node_uptime -> Returns node uptime in seconds
```

```
curl --compressed -s "http://<your_node_ext_ip>:8079/webui?as_json" -H "ACCESS_TOKEN: <your_access_token>" --output - | gunzip | jq -> Returns all data
```
```
curl --compressed -s "http://<your_node_ext_ip>:8079/webui?as_json" -H "ACCESS_TOKEN: <your_access_token>" --output - | gunzip | jq '.networks.Backbone.rewards | add' -> Calculates all your earned rewards in Backbone network
```
## Issues with the plugin

To help me debugging the plugin, the best way to do that is to provide me `webui.log` file which is generated in the plugin directory.
1. Set `debug=true` on `[webui]` section in configuration file.
2. Remove old `webui.log` from plugin directory.
3. Restart the node and wait until the plugin starts and creates the `webui.log`file.
4. Refresh the WebUI from a web browser.

## Reverse proxy with Nginx
If you have bought a domain name and want to use that for viewing the WebUI stats, you can set up a reverse proxy using Nginx. Below is an example configuration that you can adapt to your setup:

### Prerequisites
1. Domain name: Ensure your domain name is properly configured to point to your server's IP address.
2. Nginx installed.
3. OPTIONAL: SSL certificate, use a service like Let's Encrypt to secure your domain.

### Example Nginx configuration
The default configuration may conflict with your new configuration, disable it by unlinking it:
```shell
sudo unlink /etc/nginx/sites-enabled/default
```
Create the Nginx configuration file:
```shell
sudo nano /etc/nginx/sites-available/webui.conf
```
Add the following bare minimum configuration:
```shell
server {
    listen 80;
    server_name <your_domain.com>;

    location / {
        proxy_pass http://your_node_ip_addr:your_node_port/your_node_url;
    }
}
```
Enable the configuration:
```shell
sudo ln -s /etc/nginx/sites-available/webui.conf /etc/nginx/sites-enabled/
sudo nginx -t # Check for possible errors here in configuration testing
sudo systemctl reload nginx
```
Now you can verify that HTTP is working by visiting `http|https://your_domain.com`.

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

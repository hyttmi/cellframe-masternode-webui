# Changelog

## [4.08] - 2025-03-27

### Added
- Node alias to restart messages.

### Fixed
- Actually remove the heartbeat card :laughing:

## [4.07] - 2025-03-26

### Added
- Last run timestamp to cacher.
- Heartbeat module now checks the timestamp of blocks cache. If it's older than time set in `cache_age_limit` (default 2 hours), plugin will inform user via logging and Telegram/Email if enabled. This is useful for detecting if cli is timing out.

### Fixed
- Fixed issues with heartbeat module sent messages count.

### Changed
- Heartbeat card is removed and if errors are detected, error cards are shown directly on the top of the page.

## [4.06] - 2025-03-07

### Fixed
- Getting config values again, sorry :(

## [4.05] - 2025-03-07

### Fixed
- Getting config values.

## [4.04] - 2025-03-07

### Fixed
- Fixed UI issues.
- Add heartbeat module statuses to Jinja templates.

## [4.03] - 2025-02-23

### Added
- Separate function for restarting the node. **CAUTION: If node has been started manually, there's no way to restart it!**
- Heartbeat now restarts the node after 5 checks by default (configurable via heartbeat_notification_amount) if an issue is detected each time.
- WebUI template now uses `node_alias` config as header text.
- Donation button. This plugin is free and opensource and it will definitely stay that way. Please support my weekend beer drinking habit by donating a small amount of CELL tokens just to keep my mind clear and fresh ;)

## [4.02] - 2025-02-17

### Fixed
- Template whitespace trimming.

### Added
- Allow sending messages via Cellframe_Masternode_WebUI bot. Accepts one UUID or multiple ones as `list`. This one now has higher priority for message sending.

### Changed
- Some logging.
- Redirect `sys.stderr` also to `webui.log`.
- Increase sleep time of waiting for caching lock to release.
- Increase default blocks caching interval to 30 mins (like rewards caching). I promise this is the final change!
- Main threads moved back to `ThreadPool`, non-blocking this time.

## [4.01] - 2025-02-15

### Fixed
- Release cache lock always on node restart. Thanks @ageargeek for debug logs.
- Regex matching on `node_data`. Thanks @ageargeek for debug logs.

### Added
- Missing sovereign wallet information for Telegram/Email templates.
- Default values for Telegram/Email stats time (23:00)

## [4.00] - 2025-02-15

Introducing Heartbeat: A scheduled task designed to monitor node health and notify users of any issues. Currently, it tracks autocollect status and the last signed block, with plans to expand to additional monitoring features in the future.

**NOTE: Telegram notifications or Email notifications must be enabled.**

### Changed
- Cacher is not using ThreadPool anymore so commands will not run in parallel which helps especially on low end systems.
- Cacher uses locking mechanism now so blocks caching and rewards caching will never run in parallel. This one also helps on lower end systems.
- Own node in top 15 nodes chart has a different color.
- Blocks are parsed now in a separate function.

### Added
- Card for displaying main chain size. Supports KelVPN and Backbone for now.
- Card for displaying maximum weight for node on network.
- Button for removing all the cards from the view.

## [3.38] - 2025-02-08

### Fixed
- CLI version parsing.

### Changed
- Changed default cacher values again. 10 minutes to blocks, 30 minutes to rewards.

## [3.37] - 2025-02-01

### Changed
- Move blocks amount for current date to cacher, it's sometimes fast and sometimes slow so can't process it on every page refresh.
- Blocks are now cached every 5 minutes because of the above change.

### Improved
- Price fetching for tokens.

## [3.36] - 2025-01-26

### Added
- Support for retrying cli commands if timeout exceeds or some other type of error happens.
- Short timeouts for some cli commands (earlier it was 120 seconds... :/) to make sure the website opens faster.

### Changed
- `command_runner` method changed to `poller` which apparently is better for bursting commands.

### Fixed
- Properly get network name from CFNet.active_nets() objects.

## [3.35] - 2025-01-25

### Added
- Missing current block reward card.
- Card for displaying how many blocks are generated on the network for current date.

### Changed
- Change the way how rewards/blocks history is shown for the first 13 days.

## [3.34] - 2025-01-18

### Fixed
- Sovereign rewards chart.
- Rewards fetching from cache file.
- Added missing autocollect status card.

### Improved
- Rewards caching.

## [3.33] - 2025-01-16

### Fixed
- Remove a call for function which was already removed.

### Added
- Missing sovereign rewards history card.

## [3.32] - 2025-01-16

### Added
- Missing network total weight card.
- Missing network target state card.
- Missing token price card.

### Fixed
- Template was checking wrong dict for signed blocks/first signed blocks.
- Stupid mistake in cacher where it would exit the loop if network is not found. (Thanks @school_of_simple_living for debug log)

### Improved
- Blocks fetching from json file.

## [3.31] - 2025-01-15

### Fixed
- Chart fonts.
- Incorrect amount shown in sovereign rewards today.

## [3.30] - 2025-01-15

### Changed
- Layout changed completely. Now it allows you to add the cards your want, move them around and the order is saved on browsers localStorage.

## [3.26] - 2025-01-12

### Added
- Better exception logging.

### Changed
- Layout changed to separate blocks.

## [3.25] - 2025-01-10

### Added
- Node alias support. Add also alias field to config and email / Telegram templates. Thanks @BuhalexI3 for the idea!
- Even more debug logging.

### Changed
- Rearranged JS again, now chartmapping is generated also with Jinja.
- Don't show charts (rewards, blocks) if data length >= 1.
- Use `curl` to fetch external IPv4 address on `install.sh`, Arch doesn't have dig installed by default but curl seems to be there.
- Removing current day from rewards/blocks is now done on the backend (for charts).

Some other "not-so-significant" changes.

## [3.24] - 2025-01-09

### Fixed
- Chart generation.

## [3.23] - 2025-01-08

### Added
- Some extra debug logging.
- Wallet information for sovereign address.
- Rewards caching for sovereign address.
- Cards for sovereign addresses:
  - Rewards today.
  - Chart for 7,14,30,60 days.

### Improved
- Charts are now generated on the fly with Jinja.

## [3.22] - 2024-01-05

### Fixed
- Chart buttons.

## [3.21] - 2024-01-05

### Added
- Card for displaying first signed blocks for today.
- Chart for first signed blocks.

### Changed
- Blocks caching rewritten.
- Reward caching timeout increased to 6 minutes (old timeout was 2 minutes), helps with command timeouts on slow VPS's.
- Increase default time for caching start to 120 seconds (was 60 secs) before.
- HTML content is now `gzip` compressed to avoid current issues with node HTTP server.

### Improved
- Changed `startswith()` method to different type in rewards caching as apparently it's slightly faster.

## [3.20] - 2024-01-02

### Fixed
- Cast username and password to `str` to make sure login works for users who use numbers only for login.
- Missing signed blocks today.

## [3.19] - 2024-01-02

### Added
- My node, sovereign nodes and regular nodes have all different colour on node weight charts.
- Info button now bounces to visualize that it's actually clickable.
- `install.sh` now asks if you want to enable automatic updates.

### Removed
- Current date is removed from the charts now because there's already a card for displaying that information.

### Improved
- Generation of json for charts.

## [3.18] - 2024-12-31

Happy new year edition!

### Added
- Card for displaying rewards for current date. Thx once again @school_of_simple_living for the idea.
- Support for Email and Telegram custom templates which won't be overwritten on new updates. Got the idea from @John_Doe_Dev.
- Logger finally rotates files on every 5MB.

### Improved
- `install.sh` is much better again.

## [3.17] - 2024-12-29

### Fixed
- Updater, now uses Linux `cp` to copy the files.

## [3.16] - 2024-12-28

### Fixed (hopefully)
- Template issues when node_data returns nothing.

## [3.15] - 2024-12-28

### Improved
- Installation script is much better now, handles username, password and URL by default. Thx to @school_of_simple_living.

### Added
- Node weight horizontal chart in network information, your own node as a comparison with different color.

## [3.14] - 2024-12-25

### Improved
- Refined `get_node_stats` function to fetch information of all nodes.

### Added
- Top 10 nodes + your own node comparison chart behind weight scale button.
- Telegram and / or email message sending on successful plugin update.

Some other changes and improvements.

## [3.13] - 2024-12-21

### Fixed
- Autocollect rewards card.

### Changed
- Updater runs now every 2 hours.

## [3.12] - 2024-12-20

This is only a small maintenance release.

### Added
- Card for showing current reward per block (cached).
- Latest plugin version back to template rendering.
- Some more debug logging.

### Fixed
- Fixed some mistakes in code.

### Removed
- Removed the oldskool theme, it's useless!

## [3.11] - 2024-12-14

### Added
- Option for enabling automatic updater to download pre-release versions.

### Improved
- Update checking.
- Stopping the node is done by `psutil` now.

Some minor changes to other things as well

## [3.10] - 2024-12-12

### Added
- Automatic updater which downloads and extracts the latest version automatically to your node. It also automatically restarts your node after successful update.
- Installation script for easy first install.

## [3.03] - 2024-12-10

### Added
- Fetching active nodes per network
- Fetching total weight in networks (all nodes)

### Changed
- Always update cookie on login
- Removed handling of FileNotFoundError for missing network configuration, as this scenario is deemed impossible.
- Improved cards template a lot by adding much better checking for empty dicts.
- Cookie now has expiration date (14 days since login), which allows permanent logins without password if logged in once in every 14 days.
- Better conditional statements again for template

## [3.02] - 2024-12-08

### Added
- Send cookie to provide authentication on devices after first successful login

### Changed
- If username and password are empty, they are set by default to `webui` and `webui`.

### Improved
- Scheduler logic again...

## [3.01] - 2024-12-07

### Improved
- Request handlers.

### Fixed
- Telegram and Email scheduling logic.

### Changed
- Suppressed logging even more.

## [3.00] - 2024-12-06

### Added
- New cards displaying node related weight, node effective stake value.
- Some more information behind network information button (private key hash, transaction hash, sovereign tax etc.)
- Oldskool template, beware, it's pretty oldskool.

### Changed
- Backend changed massively
  - Scheduler improved massively.
  - Added much more logging and improved debug logging.
  - Separate handlers for web and JSON content.
- Javascript for charts is much better now on web template.
- Telegram and Email templates are now in the templates directory and, no more copying them between different theme directories.

### Removed
- `header_text`- It can be edited directly from templates.
- `accent_color`- It can be edited directly via CSS file.
- `json_exclude`- Keys can be removed while parsing the data from now on.
- `rate_limit` - Better to simply disable HTTP auth and use something like Nginx reverse proxy with auth + rate limiting.

## [2.100] - 2024-11-24

### Improved
- Regex again for reading wallet from network configuration file.

### Changed
- Prettify button for clearing localStorage (closed cards).
- Remove KeyError exception, `key.pop()` method changed.

## [2.99] - 2024-11-17

### Fixed
- Regex for reading network config file.

### Removed
- Node connections info from general node info, node dump shows current connections already.

## [2.98] - 2024-11-10

### Added
- Support for excluding root level keys from JSON output.
- Info button per network to show some information from node.
- Startup delay, useful for making sure node gets online and synced.
- Try, except blocks for imports and logging the errors.

### Changed
- Logging is now done via Python `logging` library.

## [2.97] - 2024-11-09

### Added
- Debug support for most necessary functions with a wrapper.
- Card for showing the node stake value currently in network.

## [2.96] - 2024-11-03

### Added
- Add support for configuring rate limit via `rate_limit_interval` configuration value.

### Changed
- Logging time format is changed to `isoformat()`.
- Moved configs to a separate class.
- Clear button for deleted cards is now opaque so it doesn't block the view unless hovered.
- Removed GMail support only and added support for any SSL/TLS capable SMTP server. **IMPORTANT: CHANGE YOUR CONFIGURATION IN `cellframe-node.cfg` FOR GMAIL**
```
smtp_server=smtp.gmail.com
smtp_port=587
smtp_password=<your_app_password>
smtp_user=<your_gmail_user>
email_use_tls=true
```
## [2.95] - 2024-10-28

### Fixed
- Cards can be removed from the view again.

## [2.94] - 2024-10-26

### Added
- `auth_bypass` setting to allow completely bypass default HTTP Authentication (useful with reverse proxy for example).
- Add scheduled blocks caching (15 minute interval) because sometimes refreshing the website takes way too long. Interval is configurable on settings (`cache_blocks_interval`).

### Changed
- Blocks and rewards are now automatically cached to a json file for better performance with 15 minute interval.
- Rename `cache_rewards_time` to `cache_rewards_interval`.
- Improve request handling.
- WebUI layout optimizations (much more responsive layout on all screen sizes).

## [2.93] - 2024-10-21

### Added
- Support for KelVPN token price, which is fetched directly from [KelVPN.com](https://kelvpn.com) for now
- Card for showing sum of all received rewards

### Changed
- All logging is now done also to `webui.log` file in plugin path
- Change favicon to black & white
- Some additional checks in template for preventing possible errors
- New Telegram template (thx @John_Doe_Dev)
- Bring back `NETWORK_TARGET_STATE`
- Add more of CPU or I/O intensive functions into `ThreadPool()` for parallel launching

### Fixed
- Use `threading.Lock()` method for avoiding possible race conditions when writing to a log file

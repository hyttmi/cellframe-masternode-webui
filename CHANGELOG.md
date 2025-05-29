# Changelog

## [5.00] - 2025-05-29

### Added
- Added offline, online, resync method to networks with failed heartbeat.
- Heartbeat now checks also if node is added to the node list with correct IP address and if not, reports to user.
- Configuration for heartbeat interval (`heartbeat_interval`, default 30 mins).
- Websocket server for real time push messages to your browser! Configure using `websocket_server_port` in configuration file, default port is `40000`.
- More modular notification system.
- Support for notifying user with statistics every `X` minutes. Shortest possible interval is 30 minutes. If set, it will override `email_stats_time` and `telegram_stats_time`.
- Card with latest signed block timestamp (locale aware).
- Custom icons! Use external url with setting `show_icon=true` and `icon_url=xxx`. By default, `icon_url` is `cpunk` logo.
- Method to check if cli is responding correctly, while not 100% bullet proof, it should increase overall responsiveness of the plugin.
- Add a button for restarting the node.
- Add handler for POST requests for allowing interacting with node in the future.

### Changed
- Default interval for heartbeat thread is now 30 minutes for allowing node to try resync method.
- Use Threadpool for fetching general info, it's at least 4 times faster now.
- Changed way how node PID is fetched, it's at least 10 times faster on Linux now.
- Installer now uses `access_token` by default, no need to save username and password anymore.

### Fixed
- Bug on setting cookie when `bypass_auth` was set.
- Bug on setting multiple cookies. (CF Python helpers issue)
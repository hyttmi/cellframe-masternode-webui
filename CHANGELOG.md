# Changelog

## [5.00] - 2025-XX-XX

### Added
- Added offline, online, resync method to networks with failed heartbeat.
- Heartbeat now checks also if node is added to the node list and if not, reports to user.
- Configuration for heartbeat interval (`heartbeat_interval`, default 30 mins).
- Websocket server for real time push messages to your browser. To enable, set `websocket_port` in configuration file.
- Much more modular notification system.
- Support for notifying user with statistics every `X` minutes. Shortest possible interval is 30 minutes. If set, it will override `email_stats_time` and `telegram_stats_time`.
- Latest signed block timestamp.
- Custom icons! Use external url with setting `show_icon=true` and `icon_url=xxx`. By default, `icon_url` is `cpunk` logo.

### Changed
- Default interval for heartbeat thread is now 30 minutes for allowing node to try resync method.

### Fixed
- Bug on setting cookie when `bypass_auth` was set.
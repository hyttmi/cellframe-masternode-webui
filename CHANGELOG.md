# Changelog

## [5.00] - 2025-XX-XX

### Added
- Added offline, online, resync method to networks with failed heartbeat.
- Configuration for heartbeat interval (`heartbeat_interval`, default 30 mins).
- Websocket server for real time push messages to your browser! Running by default on port 40000, if not available, will test next possible port until reaches port 40200. Check the assigned port from logs!

### Changed
- Default interval for heartbeat thread is now 30 minutes for allowing node to try resync method.

### Fixed
- Bug on setting cookie when `bypass_auth` was set.
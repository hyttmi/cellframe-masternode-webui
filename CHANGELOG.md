# Changelog

## [4.10] - 2025-04-02

### Added
- Cards for displaying sync percentage (or "Unknown", if value is `- %`) from zerochain and mainchain (request by @ageargeek).
- Tutorial for displaying how to use the WebUI.
- Function for checking if node is synced 100% (again).
- Show changelog after update.

### Fixed
- Updating process quirks.

### Changed
- Change updating process to be not so platform specific.
- Revert the removing of files when updating, there's no reason to do that really.
- Don't update cache if chains are not 100% synced.
- Dragging & sorting cards is not possible anymore in available cards.
- Default theme is now CPUNK. Deal with it :sunglasses:
- Update installer to create a default password for the WebUI.
- custom_templates directory is now in the root directory.

## [4.09] - 2025-03-31

### Added
- Add cool new CPUNK theme.
- Load logo (CPUNK) from S3.
- Load favicons from S3.
- Missing node address card.
- Print current configuration to log file on startup.
- Preliminary QEVM support. (Not even sure about the network name yet.)
- Pass template name too with Jinja.

### Removed
- Donation button.

### Changed
- Made themes more modular, now all scripts are in `scripts` directory and chart colours are passed with Jinja based on a template used.
- Cards are now sorted by size.
- Updater now removes old files/dirs before copying new files.

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
# Changelog

## [3.03] - 2024-12-10

### Added
- Fetching active nodes per network
- Fetching total weight in networks (all nodes)

### Changed
- Always update cookie on login
- Removed handling of FileNotFoundError for missing network configuration, as this scenario is deemed impossible.
- Improved cards template a lot by adding much better checking for empty dicts.
- Cookie now has expiration date (14 days since login), which allows permanent logins without password if logged in once in every 14 days.

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

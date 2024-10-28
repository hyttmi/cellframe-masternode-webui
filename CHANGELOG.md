
# Changelog

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
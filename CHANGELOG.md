
# Changelog

## [UNRELEASED] - 2024-10-22

### Added
- `auth_bypass` setting to allow completely bypass default HTTP Authentication (useful with reverse proxy for example)
### Changed
- Improve request handling
### Fixed

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
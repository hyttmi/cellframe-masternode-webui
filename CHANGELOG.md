# Changelog

## [5.12] - 2025-07-11

☀️ Happy holidays edition ☀️!

### Fixed
- Fixed regex parsing once again (correctly this time).
- Telegram template.

### Added
- Feature to check if node is launched as a service.

### Changed
- Disable restart button if node is not running as a service.

### Improved
- Cache node PID, node version, running as a service (True|False) on startup to speed things up.
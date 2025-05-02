# Changelog

## [4.12] - 2025-05-02

### Added
- Support for disabling automatic restart of node on failed heartbeat.
- Bypass HTTP authentication automatically from localhost.
- Some more debug logging.

### Fixed
- Fix centering of heartbeat error divs.
- Calculate sync percent now directly from `current` and `in network` values.

### Changed
- Now only main chain percent is calculated & shown in the UI as it should be enough.
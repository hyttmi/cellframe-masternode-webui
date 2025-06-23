# Changelog

## [5.11] - 2025-06-23

### Fixed
- Parsing changelog.
- Parsing `srv_stake list keys` which has dot in front of `pkey_hash` for some reason.

### Changed
- Make sure that long running commands are not possible to run via WebUI CLI.
- No more retries for CLI commands, if it fails, it fails.
- More informative messages from Heartbeat to UI.
- Focus CLI input field automatically on WebUI.
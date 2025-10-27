# Changelog

## 2025-10-27

### Fixed
- Error handling and JSON serialization for `/jobs` endpoint
- Status page error visibility and debugging
- Redirect to status page after upload
- Install bottle dependency before app start
- CUPS queue creation for IPP URIs

### Changed
- Replaced uv with standard pip and python
- Renamed from MiniPrint to Spoolcat

### Added
- GitHub Actions workflow for Docker image publishing
- CUPS queue auto-creation for IPP URIs in entrypoint
- Persistent volumes for CUPS spool and config
- Explicit JSON content-type headers

## Initial Release

- PDF upload via web interface
- CUPS printing with color and duplex options
- SQLite job tracking
- Auto-cleanup of old files
- Status page with job history

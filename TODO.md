# TODO - Rezept-Tagebuch

## Infrastructure

### Podman Pods Migration
- **Priority**: Medium
- **Status**: Blocked (waiting for Podman 5.x)
- **Description**: Migrate seaser services to use Podman Pods for better container grouping
- **Details**:
  - Current setup uses individual containers connected via seaser-network
  - Pods would allow better resource management and simplified networking
  - Attempted migration failed with Podman 4.9.3 (incompatible with Quadlets)
  - Successfully upgraded to Podman 5.7.0 (compiled from source)
  - Quadlets are working with individual containers
  - **Next Step**: Migrate to Pods once Podman 5.x Quadlets with Pods are validated
- **Related Files**:
  - `~/.config/containers/systemd/*.container` - Current Quadlet definitions
  - `docs/PODMAN-NETWORK.md` - Network documentation
- **References**:
  - Podman Quadlets: https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html
  - Pod definition: https://docs.podman.io/en/latest/markdown/podman-pod-create.1.html

## Features

### Multi-user Support
- ✅ Completed in v2.0
- User profile selection working
- Database per-user isolation implemented

## Documentation

### KI Code Review System
- ✅ Automated nightly code reviews at 02:00
- ✅ Reviews only files changed previous day
- ✅ Ollama integration with qwen2.5-coder:7b model
- ✅ Flask web interface for viewing reviews
- Located at: `https://seaser.einfachanders.rocks/reviews/`

## Maintenance

### Database Backups
- ✅ Automated daily backups configured
- PostgreSQL backup scripts in `scripts/database/`
- Backup retention policy implemented

## Notes

- Podman 5.7.0 compiled from source at `/usr/local/bin/podman`
- Using runc runtime (configured in `~/.config/containers/containers.conf`)
- All services managed via systemd user services
- Network: seaser-network (10.89.0.0/24)

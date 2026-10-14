#!/usr/bin/env sh
# Backup datado da fila, decisões, rascunhos e indicadores; mantém 30 cópias.
set -eu
ROOT="${OBSERVATORIO_ROOT:-/opt/observatorio}"
DEST="${OBSERVATORIO_BACKUP_DIR:-/var/backups/observatorio}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
install -d -m 750 "$DEST"
tar -C "$ROOT/automation" -czf "$DEST/editorial-$STAMP.tgz" inbox state review monitoring
find "$DEST" -type f -name 'editorial-*.tgz' -mtime +30 -delete

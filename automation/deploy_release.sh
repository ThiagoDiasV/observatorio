#!/usr/bin/env sh
# Esta rotina só publica um release já construído e validado.
# Não é chamada pelo coletor diário.
set -eu

SOURCE_ROOT="${1:?informe o diretório fonte do projeto}"
RELEASE_ROOT="${RELEASE_ROOT:-/var/www/bozo/releases}"
CURRENT_LINK="${CURRENT_LINK:-/var/www/bozo/current}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RELEASE="$RELEASE_ROOT/$STAMP"

cd "$SOURCE_ROOT"
python3 build.py
python3 verify.py
test -f dist/index.html

install -d -m 755 "$RELEASE"
tar -C dist -cf - . | tar -C "$RELEASE" -xf -
find "$RELEASE" -type d -exec chmod 755 {} +
find "$RELEASE" -type f -exec chmod 644 {} +
ln -sfn "$RELEASE" "${CURRENT_LINK}.next"
mv -Tf "${CURRENT_LINK}.next" "$CURRENT_LINK"

#!/bin/sh
set -eu
D="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec "$D/install.sh" --target=ew1200g-pro "$@"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="$ROOT_DIR/Cloudhabil_CLI_patch.tar.gz"

# Create a source archive excluding VCS and other ignored files
tar --exclude-vcs --exclude-from="$ROOT_DIR/.gitignore" -czf "$OUTPUT" -C "$ROOT_DIR" .

echo "Created $OUTPUT"

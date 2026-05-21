#!/usr/bin/env bash
# this_file: publish.sh
# Bump the git tag (semver), build, and publish vecssy-slim to PyPI.
# Version is derived from git tags by hatch-vcs, so the tag bump must come first.
set -euo pipefail
cd "$(dirname "$0")"

uvx hatch clean
uvx gitnextver .
uv build
uv publish

#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC2035
rm -rf dist build *.egg-info
python -m build
python -m twine check dist/*
echo ""
echo "Built artifacts:"
ls -lh dist
echo ""
echo "To install with pipx:"
# shellcheck disable=SC2012
echo "  pipx install --force dist/$(ls -1 dist/*.whl | tail -n 1)"

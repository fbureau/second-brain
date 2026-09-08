#!/usr/bin/env bash
# Run the second-brain plugin conformance suite (no Hermes needed).
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 -m unittest discover -s hermes/tests -v

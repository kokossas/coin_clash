#!/bin/bash
# Run all tests from the project root
cd "$(dirname "$0")"
python -m pytest backend/tests/ core/tests/ -v "$@"

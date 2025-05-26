#!/bin/bash

# Run pytest for all tests in the backend directory
cd /home/ubuntu/coin_clash/backend
python -m pytest tests/ -v

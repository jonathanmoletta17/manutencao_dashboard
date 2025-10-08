#!/bin/sh
set -e

# Inicia backend (uvicorn) em background
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8010 &

# Inicia Nginx em primeiro plano
nginx -g 'daemon off;'
#!/bin/bash

echo "Starting MCU AI Assistant backend..."

cd "$(dirname "$0")"

uvicorn app:app --reload --port 8000
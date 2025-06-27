#!/bin/bash

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    set -a
    source .env
    set +a
else
    echo "Warning: .env file not found"
fi

# Run the seeding script
echo "Running database seeding..."
python scripts/seed_database.py

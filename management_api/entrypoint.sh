#!/bin/bash

# Initialize the database
python -m src.opmas_mgmt_api.db.init_db

# Start the API server
exec uvicorn opmas_mgmt_api.main:app --host 0.0.0.0 --port 8000 
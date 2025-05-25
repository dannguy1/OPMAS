#!/bin/bash

# Function to create user and database
create_db_user() {
    local username=$1
    local password=$2
    local dbname=$3

    echo "Creating user $username and database $dbname..."

    # Create user
    psql -v ON_ERROR_STOP=1 <<-EOSQL
        DO
        \$do\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$username') THEN
                CREATE USER $username WITH PASSWORD '$password';
            END IF;
        END
        \$do\$;
EOSQL

    # Create database
    psql -v ON_ERROR_STOP=1 <<-EOSQL
        DO
        \$do\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '$dbname') THEN
                CREATE DATABASE $dbname OWNER $username;
            END IF;
        END
        \$do\$;
EOSQL

    # Grant privileges
    psql -v ON_ERROR_STOP=1 <<-EOSQL
        GRANT ALL PRIVILEGES ON DATABASE $dbname TO $username;
EOSQL
}

# Read configuration
DEV_USER=$(grep -A 5 "development:" config/database.yaml | grep "user:" | awk '{print $2}')
DEV_PASS=$(grep -A 5 "development:" config/database.yaml | grep "password:" | awk '{print $2}')
DEV_DB=$(grep -A 5 "development:" config/database.yaml | grep "name:" | awk '{print $2}')

TEST_USER=$(grep -A 5 "test:" config/database.yaml | grep "user:" | awk '{print $2}')
TEST_PASS=$(grep -A 5 "test:" config/database.yaml | grep "password:" | awk '{print $2}')
TEST_DB=$(grep -A 5 "test:" config/database.yaml | grep "name:" | awk '{print $2}')

PROD_USER=$(grep -A 5 "production:" config/database.yaml | grep "user:" | awk '{print $2}')
PROD_PASS=$(grep -A 5 "production:" config/database.yaml | grep "password:" | awk '{print $2}')
PROD_DB=$(grep -A 5 "production:" config/database.yaml | grep "name:" | awk '{print $2}')

# Create users and databases
create_db_user "$DEV_USER" "$DEV_PASS" "$DEV_DB"
create_db_user "$TEST_USER" "$TEST_PASS" "$TEST_DB"
create_db_user "$PROD_USER" "$PROD_PASS" "$PROD_DB"

echo "Database setup complete!"

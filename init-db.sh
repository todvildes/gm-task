#!/bin/bash
set -e

# Create the users database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE users;
    GRANT ALL PRIVILEGES ON DATABASE users TO postgres;
EOSQL

# Create the users_test database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE users_test;
    GRANT ALL PRIVILEGES ON DATABASE users_test TO postgres;
EOSQL

echo "PostgreSQL initialization completed" 

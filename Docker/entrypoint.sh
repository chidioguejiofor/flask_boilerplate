#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u

get_db_params() {
  #  get the database params needed to check if the database has initialized.
  DB_HOST=$(awk -F@ '{print $2}' <<<"${DATABASE_URL}" | awk -F/ '{print $1}' |
    awk -F: '{print $1}')
  DB_PORT=$(awk -F@ '{print $2}' <<<"${DATABASE_URL}" | awk -F/ '{print $1}' |
    awk -F: '{print $2}')
}

wait_for_db() {
  #  Waits for database to connect
  get_db_params
  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 2
  done
}

migration() {
  #  Wait for database to start up then run migration
  wait_for_db
  flask db upgrade
}

start() {
  #  Start the API based on the selected environment
  if [[ $FLASK_ENV == "production" ]] || [[ $FLASK_ENV == "staging" ]]; then
    supervisord -c /usr/local/etc/supervisord.conf
  else
    flask run --host=0.0.0.0
  fi
}

main() {
  #  Main function to rule them all
  migration
  start
}

#  main function call
main

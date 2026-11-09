#!/bin/bash

scripts/seed_database.sh ${@}

exec "${@}"

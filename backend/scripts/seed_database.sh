#!/bin/bash

if [[ "$1" == *"celery" ]]; then
	# do not seed the database when running celery workers
	exit 0
fi

if [ -z "$ADMIN_PASSWORD" ]; then
	echo "\$ADMIN_PASSWORD not set"
	echo "Do you have the .env in your directory?"
fi
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"

echo "Performing Migrations"
python3 manage.py migrate --noinput
echo "Creating Users"
python3 manage.py shell <<EOF
from django.contrib.auth.models import User
User.objects.all().delete()
User.objects.create_superuser('admin', email='', password='$ADMIN_PASSWORD')
User.objects.create_user('mod', password='$MOD_PASSWORD')
EOF

if [ "$ADMIN_PASSWORD" == "admin" ]; then
	echo 1>&2
	echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" 1>&2
	echo "! Warning! Default admin password used, change it! !" 1>&2
	echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" 1>&2
	echo 1>&2
fi
if [ "$MOD_PASSWORD" == "mod" ]; then
	echo "! Warning! Default  mod  password used, change it! !" 1>&2
	echo 1>&2
fi
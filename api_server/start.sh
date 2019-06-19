#!/bin/bash

cd /home/q/Documents/recycle_bin/api_server
mkdir /run/recycle_bin
chown q /run/recycle_bin
chmod 775 /run/recycle_bin
sudo -u q -g www-data bash <<EOF
python3 manage.py collectstatic --noinput
python3 manage.py migrate
uwsgi --ini server.ini
EOF

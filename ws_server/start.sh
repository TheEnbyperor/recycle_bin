#!/bin/bash

mkdir /data/recycle_bin
chown -R q:q /data/recycle_bin

sudo -i -u q bash <<EOF
cd /opt/recycle_bin/ws_server/venv
exec /opt/recycle_bin/ws_server/venv/bin/python /opt/recycle_bin/ws_server/main.py --debug --config /data/recycle_bin/config.db --server https://recycle-bin.home.misell.cymru/graphql/
EOF

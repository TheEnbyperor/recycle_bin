#!/bin/bash

if [ ! -f /data/recycle_bin/config.db ]; then
  cp /opt/recycle_bin/ws_server/config.db /data/recycle_bin/config.db
fi

sudo -i -u q bash <<EOF
cd /opt/recycle_bin/ws_server/venv
exec /opt/recycle_bin/ws_server/venv/bin/python3 /opt/recycle_bin/ws_server/main.py --debug --config /data/recycle_bin/config.db
EOF
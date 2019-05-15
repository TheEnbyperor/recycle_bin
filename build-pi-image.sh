#!/bin/bash

SYSTEM_IMAGE=$1

# Build web UI
echo "Building web UI"
cd bin_ui && yarn build && cd ..

# Mount image
echo "Mounting image"
mkdir root_system
sudo mount $SYSTEM_IMAGE root_system && sudo cp /usr/bin/qemu-arm-static root_system/usr/bin

# System updates
echo "Installing system updates"
sudo chroot root_system /bin/bash <<EOF
apt update && apt upgrade -y
EOF

# Install web UI
echo "Installing web UI"
mkdir -p root_system/opt/recycle_bin/
sudo rm -rf root_system/opt/recycle_bin/web_ui
sudo cp -a bin_ui/build root_system/opt/recycle_bin/web_ui
sudo chroot root_system /bin/bash <<EOF
chown -R root:root /opt/recycle_bin/web_ui
EOF

# Install WS Server
echo "Installing websocket server"
sudo rm -rf root_system/opt/recycle_bin/ws_server
sudo cp -a ws_server root_system/opt/recycle_bin/ws_server
sudo chroot root_system /bin/bash <<EOF
chown -R root:root /opt/recycle_bin/ws_server
python3 -m pip install virtualenv
cd /opt/recycle_bin/ws_server
virtualenv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
EOF

# Install config
echo "Installing various config files"
sudo cp config/openbox_autostart root_system/home/q/.config/openbox/autostart
sudo chmod +x root_system/home/q/.config/openbox/autostart
sudo cp config/nginx root_system/etc/nginx/sites-available/default
sudo cp config/ws_server.service root_system/etc/systemd/system/
sudo chroot root_system /bin/bash <<EOF
chown -R q:q /home/q/.config/openbox/autostart
chown -R root:root /etc/nginx/sites-available/default
chown -R root:root /etc/systemd/system/ws_server.service
systemctl enable ws_server
EOF

# Cleanup
echo "Cleaning up"
sudo rm root_system/usr/bin/qemu-arm-static
sudo umount root_system
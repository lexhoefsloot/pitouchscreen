#!/bin/bash

# Update and install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip git unclutter

# Clone the repository
git clone https://github.com/lexhoefsloot/pitouchscreen.git
cd pitouchscreen

# Install Python packages
sudo pip3 install evdev RPi.GPIO

# Copy and set permissions for the backlight script
sudo cp backlight.py /usr/local/bin/backlight.py
sudo chmod +x /usr/local/bin/backlight.py

# Create and enable the systemd service for backlight control
echo -e "[Unit]\nDescription=Touchscreen Backlight Control\nAfter=multi-user.target\n\n[Service]\nType=simple\nExecStart=/usr/bin/python3 /usr/local/bin/backlight.py\nRestart=always\nUser=root\n\n[Install]\nWantedBy=multi-user.target" | sudo tee /etc/systemd/system/backlight.service
sudo systemctl daemon-reload
sudo systemctl enable backlight.service
sudo systemctl start backlight.service

# Configure unclutter
sudo sh -c 'echo -e "DISPLAY=:0.0 ; export DISPLAY\nunclutter -idle 0.01 -root" >> /etc/X11/xinit/xinitrc'

# Set the URL for FullPageOS
sudo sh -c 'echo "http://homeassistant.local:8123/dashboard-livingroom/0" > /boot/fullpageos.txt'

# Store VNC password
x11vnc -storepasswd

echo "Installation complete! The backlight service is now running and will start on boot."

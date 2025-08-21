#!/bin/bash
# Setup KVM for Android emulator on Linux

set -e

echo "Setting up KVM for Android emulator on Linux..."

# Configure KVM permissions
echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' | \
  sudo tee /etc/udev/rules.d/99-kvm4all.rules

# Reload and apply udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger --name-match=kvm

echo "KVM setup completed successfully"

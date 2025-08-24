#!/bin/bash
# Setup KVM for Android emulator on Linux

set -e

echo "Setting up KVM for Android emulator on Linux..."

# Check if KVM is available
if [ ! -e /dev/kvm ]; then
    echo "Warning: /dev/kvm not found. Checking CPU virtualization support..."

    # Check if virtualization is supported
    if grep -E 'vmx|svm' /proc/cpuinfo > /dev/null; then
        echo "CPU supports virtualization. Attempting to load KVM module..."

        # Try to load KVM module based on CPU type
        if grep -E 'vmx' /proc/cpuinfo > /dev/null; then
            sudo modprobe kvm_intel || true
        elif grep -E 'svm' /proc/cpuinfo > /dev/null; then
            sudo modprobe kvm_amd || true
        fi

        # For ARM systems
        if [ "$(uname -m)" = "aarch64" ] || [ "$(uname -m)" = "arm64" ]; then
            echo "ARM64 system detected. Loading KVM for ARM..."
            sudo modprobe kvm || true
        fi
    else
        echo "Warning: CPU does not support hardware virtualization"
        echo "Android emulator will run in software emulation mode (slower)"
    fi
fi

# Only configure KVM if it exists
if [ -e /dev/kvm ]; then
    echo "Configuring KVM permissions..."

    # Configure KVM permissions
    echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' | \
      sudo tee /etc/udev/rules.d/99-kvm4all.rules

    # Reload and apply udev rules
    sudo udevadm control --reload-rules || true
    sudo udevadm trigger --name-match=kvm || true

    # Verify KVM access
    if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
        echo "✓ KVM setup completed successfully"
        ls -la /dev/kvm
    else
        echo "Warning: KVM device exists but may not have correct permissions"
        ls -la /dev/kvm || true
    fi
else
    echo "Warning: KVM not available. Emulator will use software acceleration."
    echo "This is expected on some CI environments and ARM systems."
    exit 0  # Don't fail the build
fi

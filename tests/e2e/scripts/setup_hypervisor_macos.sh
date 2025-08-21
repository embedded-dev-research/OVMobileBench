#!/bin/bash
# Setup Hypervisor.framework for Android emulator on macOS

set -e

echo "Checking Hypervisor.framework for Android emulator on macOS..."

# Hypervisor.framework is enabled by default on GitHub Actions macOS runners
# Just verify it's available
if sysctl -n kern.hv_support 2>/dev/null; then
    echo "Hypervisor.framework is available and enabled"
else
    echo "Hypervisor.framework not available"
    echo "Note: This may affect emulator performance"
fi

echo "Hypervisor.framework check completed"

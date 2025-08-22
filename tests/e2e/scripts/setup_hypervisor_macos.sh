#!/bin/bash
# Setup Hypervisor.framework for Android emulator on macOS

set -e

echo "Checking Hypervisor.framework for Android emulator on macOS..."

# Check if Hypervisor.framework is available
HV_SUPPORT=$(sysctl -n kern.hv_support 2>/dev/null || echo "0")

if [ "$HV_SUPPORT" = "1" ]; then
    echo "✓ Hypervisor.framework is available and enabled"
    echo "  Hardware acceleration will be used for Android emulator"
else
    echo "⚠️  Hypervisor.framework is not available"
    echo "  Note: The emulator will run without hardware acceleration (slower performance)"
    echo "  This is unexpected on macOS runners and may indicate a configuration issue"
fi

# Additional diagnostics for debugging
echo ""
echo "System information:"
echo "  Architecture: $(uname -m)"
echo "  macOS version: $(sw_vers -productVersion 2>/dev/null || echo 'unknown')"
echo "  Virtualization support: $HV_SUPPORT"

echo ""
echo "Hypervisor.framework check completed"

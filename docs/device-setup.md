# Device Setup Guide

This guide covers setting up Android and Linux ARM devices for benchmarking with OVMobileBench.

## Table of Contents

1. [Android Device Setup](#android-device-setup)
2. [Linux ARM Device Setup](#linux-arm-device-setup)
3. [Device Stabilization](#device-stabilization)
4. [Performance Tuning](#performance-tuning)
5. [Multiple Device Setup](#multiple-device-setup)
6. [Troubleshooting](#troubleshooting)

## Android Device Setup

### Prerequisites

- Android device with ARM64 processor
- USB cable for connection
- Android SDK Platform Tools installed on host

### Step 1: Enable Developer Options

1. Go to **Settings → About Phone**
2. Tap **Build Number** 7 times
3. Enter your PIN/password if prompted
4. Developer Options will appear in Settings

### Step 2: Enable USB Debugging

1. Go to **Settings → Developer Options**
2. Enable **Developer Options** toggle
3. Enable **USB Debugging**
4. (Optional) Enable **Stay Awake** to keep screen on while charging

### Step 3: Connect Device

1. Connect device via USB cable
2. Select **File Transfer** or **MTP** mode
3. Accept the RSA fingerprint dialog on device

### Step 4: Verify Connection

```bash
# List connected devices
adb devices

# Expected output:
# List of devices attached
# R3CN30XXXX  device

# Get device information
adb shell getprop ro.product.model
adb shell getprop ro.product.cpu.abi
adb shell getprop ro.build.version.release
```

### Step 5: Prepare Device Environment

```bash
# Create working directory
adb shell mkdir -p /data/local/tmp/ovmobilebench

# Verify write permissions
adb shell touch /data/local/tmp/ovmobilebench/test.txt
adb shell rm /data/local/tmp/ovmobilebench/test.txt

# Check available storage
adb shell df -h /data/local/tmp
```

### Android-Specific Configuration

```yaml
device:
  kind: "android"
  serials: ["R3CN30XXXX"]  # From 'adb devices'
  push_dir: "/data/local/tmp/ovmobilebench"
  use_root: false
  env_vars:
    LD_LIBRARY_PATH: "/data/local/tmp/ovmobilebench/lib:$LD_LIBRARY_PATH"
```

### Common Android Devices

| Device | SoC | CPU Cores | Recommended Config |
|--------|-----|-----------|-------------------|
| Pixel 6 | Google Tensor | 2x X1 + 2x A76 + 4x A55 | threads: 4-8 |
| Galaxy S21 | Snapdragon 888 | 1x X1 + 3x A78 + 4x A55 | threads: 4-8 |
| OnePlus 9 | Snapdragon 888 | 1x X1 + 3x A78 + 4x A55 | threads: 4-8 |
| Xiaomi 11 | Snapdragon 888 | 1x X1 + 3x A78 + 4x A55 | threads: 4-8 |

## Linux ARM Device Setup

### Prerequisites

- Linux ARM device (Raspberry Pi, Jetson, etc.)
- SSH access to device
- Sufficient storage space

### Step 1: Enable SSH

#### Raspberry Pi
```bash
# On Raspberry Pi
sudo systemctl enable ssh
sudo systemctl start ssh
```

#### Ubuntu/Debian
```bash
sudo apt-get install openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh
```

### Step 2: Set Up SSH Keys

```bash
# On host machine
# Generate SSH key if needed
ssh-keygen -t rsa -b 4096

# Copy key to device
ssh-copy-id user@device.local

# Test connection
ssh user@device.local "echo 'Connection successful'"
```

### Step 3: Prepare Device Environment

```bash
# Create working directory
ssh user@device.local "mkdir -p ~/ovmobilebench"

# Install dependencies
ssh user@device.local "sudo apt-get update && sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    wget"

# Check system info
ssh user@device.local "uname -a && lscpu"
```

### Linux SSH Configuration

```yaml
device:
  kind: "linux_ssh"
  host: "192.168.1.100"  # Or hostname
  port: 22
  user: "ubuntu"
  key_path: "~/.ssh/id_rsa"
  push_dir: "/home/ubuntu/ovmobilebench"
  env_vars:
    LD_LIBRARY_PATH: "/home/ubuntu/ovmobilebench/lib:$LD_LIBRARY_PATH"
```

### Common Linux ARM Devices

| Device | SoC | CPU | RAM | Recommended Config |
|--------|-----|-----|-----|-------------------|
| Raspberry Pi 4 | BCM2711 | 4x Cortex-A72 | 4-8GB | threads: 4 |
| Jetson Nano | Tegra X1 | 4x Cortex-A57 | 4GB | threads: 4 |
| Jetson Xavier NX | Xavier | 6x Carmel | 8GB | threads: 6 |
| Rock Pi 4 | RK3399 | 2x A72 + 4x A53 | 4GB | threads: 4-6 |

## Device Stabilization

### Android Stabilization

#### Disable Animations
```bash
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0
```

#### Screen Management
```bash
# Turn screen off
adb shell input keyevent 26

# Set screen timeout to maximum
adb shell settings put system screen_off_timeout 2147483647

# Reduce brightness
adb shell settings put system screen_brightness 0
```

#### Network Management
```bash
# Enable airplane mode (may require root)
adb shell settings put global airplane_mode_on 1

# Disable WiFi
adb shell svc wifi disable

# Disable mobile data
adb shell svc data disable
```

#### Background Apps
```bash
# Stop unnecessary services
adb shell am force-stop com.android.chrome
adb shell am force-stop com.google.android.gms

# Clear RAM (requires root)
adb shell "echo 3 > /proc/sys/vm/drop_caches"
```

### Linux Stabilization

#### CPU Governor
```bash
# Check available governors
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors

# Set performance governor
sudo cpupower frequency-set -g performance

# Or manually for each core
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance | sudo tee $cpu
done
```

#### Disable CPU Throttling
```bash
# Disable turbo boost (Intel)
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

# Set max frequency
sudo cpupower frequency-set -f max
```

## Performance Tuning

### Android Performance

#### CPU Affinity (Root Required)
```bash
# Pin to big cores (device-specific)
# Example for Snapdragon 888 (cores 4-7 are big)
adb shell "taskset 0xF0 benchmark_app ..."
```

#### Memory Settings
```bash
# Increase memory limits (root)
adb shell "echo 2048 > /proc/sys/vm/min_free_kbytes"
adb shell "echo 0 > /proc/sys/vm/swappiness"
```

#### Thermal Management
```bash
# Monitor temperature
adb shell "cat /sys/class/thermal/thermal_zone0/temp"

# Check throttling status
adb shell dumpsys thermalservice
```

### Linux Performance

#### NUMA Affinity
```bash
# Check NUMA nodes
numactl --hardware

# Pin to specific node
numactl --cpunodebind=0 --membind=0 benchmark_app
```

#### IRQ Affinity
```bash
# Move IRQs away from benchmark cores
echo 1 | sudo tee /proc/irq/default_smp_affinity
```

#### Huge Pages
```bash
# Enable transparent huge pages
echo always | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
```

## Multiple Device Setup

### Android Device Farm

#### USB Hub Setup
```bash
# List all connected devices
adb devices -l

# Run commands on specific device
adb -s R3CN30XXXX shell "command"
```

#### Parallel Configuration
```yaml
device:
  kind: "android"
  serials:
    - "R3CN30XXXX"  # Pixel 6
    - "1234567890"  # Galaxy S21
    - "ABCDEF1234"  # OnePlus 9
  push_dir: "/data/local/tmp/ovmobilebench"
```

#### Device Identification Script
```bash
#!/bin/bash
# identify_devices.sh

for serial in $(adb devices | grep device$ | cut -f1); do
    echo "Device: $serial"
    adb -s $serial shell getprop ro.product.model
    adb -s $serial shell getprop ro.product.cpu.abi
    echo "---"
done
```

### Linux SSH Farm

#### Multiple Host Configuration
```yaml
# Use environment variables for different hosts
device:
  kind: "linux_ssh"
  host: "${TARGET_HOST}"
  user: "${TARGET_USER}"
  key_path: "~/.ssh/id_rsa"
```

#### Ansible Inventory
```ini
[arm_devices]
rpi4-1 ansible_host=192.168.1.101 ansible_user=pi
rpi4-2 ansible_host=192.168.1.102 ansible_user=pi
jetson-1 ansible_host=192.168.1.110 ansible_user=ubuntu
```

## Troubleshooting

### Android Issues

#### Device Not Found
```bash
# Restart ADB server
adb kill-server
adb start-server

# Check USB connection
lsusb | grep -i google  # For Pixel devices

# Try different USB port/cable
```

#### Permission Denied
```bash
# Check SELinux status
adb shell getenforce

# Temporarily set permissive (root)
adb shell setenforce 0

# Use alternative directory
adb shell mkdir -p /sdcard/ovmobilebench
```

#### Insufficient Storage
```bash
# Check available space
adb shell df -h

# Clear cache
adb shell pm clear com.android.systemui

# Use external storage
adb shell mkdir -p /sdcard/Android/data/ovmobilebench
```

### Linux SSH Issues

#### Connection Refused
```bash
# Check SSH service
sudo systemctl status ssh

# Check firewall
sudo ufw status

# Allow SSH
sudo ufw allow 22/tcp
```

#### Authentication Failed
```bash
# Check key permissions
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Verify key
ssh-keygen -l -f ~/.ssh/id_rsa

# Test with password
ssh -o PreferredAuthentications=password user@host
```

#### Slow Transfer
```bash
# Use compression
scp -C file user@host:/path

# Check network
ping -c 10 device.local

# Use rsync instead
rsync -avz --progress file user@host:/path
```

## Device Health Monitoring

### Android Monitoring Script
```bash
#!/bin/bash
# monitor_android.sh

SERIAL=$1
while true; do
    # Temperature
    TEMP=$(adb -s $SERIAL shell cat /sys/class/thermal/thermal_zone0/temp)
    echo "Temp: $((TEMP/1000))°C"
    
    # Battery
    BATTERY=$(adb -s $SERIAL shell dumpsys battery | grep level)
    echo "Battery: $BATTERY"
    
    # CPU frequency
    FREQ=$(adb -s $SERIAL shell cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)
    echo "CPU Freq: $((FREQ/1000)) MHz"
    
    sleep 5
done
```

### Linux Monitoring Script
```bash
#!/bin/bash
# monitor_linux.sh

while true; do
    # Temperature
    sensors | grep "Core"
    
    # CPU frequency
    cpupower frequency-info | grep "current CPU"
    
    # Memory
    free -h | grep Mem
    
    # Load average
    uptime
    
    sleep 5
done
```

## Best Practices

1. **Consistency**: Use same device state for all benchmarks
2. **Isolation**: Minimize background activity
3. **Thermal**: Allow cooldown between runs
4. **Power**: Use consistent charging state
5. **Documentation**: Record device configuration
6. **Validation**: Verify setup before benchmarking
7. **Automation**: Script repetitive setup tasks
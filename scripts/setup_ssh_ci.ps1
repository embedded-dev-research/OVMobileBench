# Setup SSH for CI testing on Windows
# This script configures OpenSSH for Windows CI environments

$ErrorActionPreference = "Stop"

Write-Host "Setting up SSH server for Windows CI..."

# Create .ssh directory
$sshDir = "$env:USERPROFILE\.ssh"
New-Item -ItemType Directory -Force -Path $sshDir | Out-Null

# Generate SSH keys if not exist
$idRsaPath = "$sshDir\id_rsa"
if (-not (Test-Path $idRsaPath)) {
    Write-Host "Generating SSH keys..."
    ssh-keygen -t rsa -b 3072 -f $idRsaPath -N '""' -q
}

# Setup authorized_keys
$authorizedKeysPath = "$sshDir\authorized_keys"
Copy-Item "$idRsaPath.pub" -Destination $authorizedKeysPath -Force

# Set permissions
Write-Host "Setting file permissions..."
icacls $sshDir /inheritance:r /grant "${env:USERNAME}:F" | Out-Null
icacls $idRsaPath /inheritance:r /grant "${env:USERNAME}:F" | Out-Null
icacls $authorizedKeysPath /inheritance:r /grant "${env:USERNAME}:F" | Out-Null

# Install OpenSSH Server
Write-Host "Installing OpenSSH Server..."
$capability = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'

if ($capability.State -ne "Installed") {
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
    Write-Host "OpenSSH Server installed"
    Start-Sleep -Seconds 5
}

# Start SSH service
Write-Host "Starting SSH service..."
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'

# Wait for service to fully start
Start-Sleep -Seconds 3

# Configure sshd_config for key authentication
$sshdConfig = "$env:ProgramData\ssh\sshd_config"
Write-Host "Configuring sshd_config at: $sshdConfig"

# Backup original config
Copy-Item $sshdConfig "$sshdConfig.bak" -Force

# Read and modify config
$config = Get-Content $sshdConfig

# Enable key authentication and disable password
$newConfig = @()
$modified = $false

foreach ($line in $config) {
    if ($line -match "^#?PubkeyAuthentication") {
        $newConfig += "PubkeyAuthentication yes"
        $modified = $true
    }
    elseif ($line -match "^#?PasswordAuthentication") {
        $newConfig += "PasswordAuthentication no"
        $modified = $true
    }
    elseif ($line -match "^#?StrictModes") {
        $newConfig += "StrictModes no"
        $modified = $true
    }
    elseif ($line -match "^#?AuthorizedKeysFile") {
        # Comment out default to use administrators_authorized_keys
        $newConfig += "#$line"
    }
    else {
        $newConfig += $line
    }
}

# Add our settings if not found
if (-not $modified) {
    $newConfig += ""
    $newConfig += "# Added by setup_ssh_ci.ps1"
    $newConfig += "PubkeyAuthentication yes"
    $newConfig += "PasswordAuthentication no"
    $newConfig += "StrictModes no"
}

# Write new config
$newConfig | Set-Content $sshdConfig -Force

# For Windows, administrators use a different authorized_keys location
$adminAuthKeys = "$env:ProgramData\ssh\administrators_authorized_keys"
Write-Host "Setting up administrators_authorized_keys at: $adminAuthKeys"

# Copy the public key
Copy-Item "$authorizedKeysPath" -Destination $adminAuthKeys -Force

# Set correct permissions for administrators_authorized_keys
icacls $adminAuthKeys /inheritance:r | Out-Null
icacls $adminAuthKeys /grant "SYSTEM:F" | Out-Null
icacls $adminAuthKeys /grant "BUILTIN\Administrators:F" | Out-Null

# Restart SSH service to apply changes
Write-Host "Restarting SSH service..."
Restart-Service sshd -Force
Start-Sleep -Seconds 3

# Verify service is running
$service = Get-Service -Name sshd
if ($service.Status -ne 'Running') {
    throw "SSH service failed to start!"
}

Write-Host "SSH service is running"

# Test SSH connection with proper error handling
Write-Host "Testing SSH connection..."
$maxAttempts = 5

for ($i = 1; $i -le $maxAttempts; $i++) {
    Write-Host "Connection attempt $i/$maxAttempts..."
    
    try {
        $result = ssh -o StrictHostKeyChecking=no `
                     -o UserKnownHostsFile=nul `
                     -o ConnectTimeout=5 `
                     -o PasswordAuthentication=no `
                     -o PubkeyAuthentication=yes `
                     -i "$idRsaPath" `
                     localhost "echo 'SSH_WORKS'" 2>&1 | Out-String
        
        if ($result -match "SSH_WORKS") {
            Write-Host "SUCCESS: SSH connection working!"
            exit 0
        }
        
        Write-Host "Output: $result"
        
        if ($result -match "Permission denied") {
            Write-Host "Authentication failed. Debugging..."
            Write-Host "Checking key files:"
            Get-ChildItem $sshDir
            Get-ChildItem "$env:ProgramData\ssh" | Where-Object Name -like "*authorized*"
        }
    }
    catch {
        Write-Host "Error: $_"
    }
    
    if ($i -lt $maxAttempts) {
        Write-Host "Retrying in 3 seconds..."
        Start-Sleep -Seconds 3
    }
}

# If we get here, SSH test failed
throw "SSH connection test failed after $maxAttempts attempts!"
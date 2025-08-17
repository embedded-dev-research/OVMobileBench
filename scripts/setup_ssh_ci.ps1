# Setup SSH for CI testing on Windows
# This script configures OpenSSH for Windows CI environments

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

# Set basic permissions using icacls (more compatible)
try {
    icacls $authorizedKeysPath /inheritance:r /grant "${env:USERNAME}:F" 2>$null | Out-Null
    icacls $idRsaPath /inheritance:r /grant "${env:USERNAME}:F" 2>$null | Out-Null
} catch {
    Write-Host "Warning: Could not set file permissions"
}

# Check if OpenSSH Server is installed (with error handling)
try {
    $capability = Get-WindowsCapability -Online -ErrorAction Stop | Where-Object Name -like 'OpenSSH.Server*'
    $isInstalled = $capability.State -eq 'Installed'
} catch {
    Write-Host "Warning: Could not check OpenSSH capability (requires admin rights)"
    # Check if sshd service exists as fallback
    $service = Get-Service -Name sshd -ErrorAction SilentlyContinue
    $isInstalled = $null -ne $service
}

if ($isInstalled) {
    Write-Host "OpenSSH Server is installed"
    
    # Try to configure and start the service
    try {
        # Ensure service exists
        $service = Get-Service -Name sshd -ErrorAction SilentlyContinue
        if ($service) {
            # Start the service
            if ($service.Status -ne 'Running') {
                Start-Service sshd -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
            }
            
            # Configure sshd_config if we have permissions
            $sshdConfig = "C:\ProgramData\ssh\sshd_config"
            if (Test-Path $sshdConfig) {
                try {
                    # Backup original config
                    Copy-Item $sshdConfig "$sshdConfig.bak" -Force -ErrorAction SilentlyContinue
                    
                    # Read current config
                    $config = Get-Content $sshdConfig -ErrorAction SilentlyContinue
                    
                    # Ensure PubkeyAuthentication is enabled
                    if ($config -notmatch "^PubkeyAuthentication yes") {
                        Add-Content -Path $sshdConfig -Value "PubkeyAuthentication yes" -ErrorAction SilentlyContinue
                    }
                    
                    # Restart service to apply changes
                    Restart-Service sshd -ErrorAction SilentlyContinue
                    Write-Host "SSH service configured and started"
                } catch {
                    Write-Host "Warning: Could not modify sshd_config (permission denied)"
                }
            }
        }
    } catch {
        Write-Host "Warning: Could not configure SSH service: $_"
    }
} else {
    Write-Host "OpenSSH Server is not installed"
    Write-Host "Attempting to install OpenSSH Server..."
    
    # Try to install (requires admin rights)
    try {
        Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 -ErrorAction Stop
        Start-Service sshd -ErrorAction SilentlyContinue
        Set-Service -Name sshd -StartupType 'Automatic' -ErrorAction SilentlyContinue
        Write-Host "OpenSSH Server installed successfully"
    } catch {
        Write-Host "Warning: Could not install OpenSSH Server (requires admin rights)"
        Write-Host "SSH tests will be limited"
    }
}

# Test SSH connection
Write-Host "Testing SSH connection..."
$testResult = $false

for ($i = 1; $i -le 3; $i++) {
    try {
        $result = ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=nul -o ConnectTimeout=5 `
                     -i "$idRsaPath" localhost "echo SSH_OK" 2>$null
        
        if ($result -eq "SSH_OK") {
            Write-Host "SSH connection test successful!"
            $testResult = $true
            break
        }
    } catch {
        Write-Host "SSH connection attempt $i failed"
    }
    
    if ($i -lt 3) {
        Start-Sleep -Seconds 2
    }
}

if (-not $testResult) {
    Write-Host "Warning: SSH connection test failed, but setup completed"
    Write-Host "SSH keys are configured at: $sshDir"
}

exit 0
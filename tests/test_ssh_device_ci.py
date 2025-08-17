#!/usr/bin/env python3
"""Test SSH device connectivity in CI environment using Paramiko test server."""

import os
import sys
import socket
import threading
import time
from pathlib import Path
import paramiko


class DemoSSHServer(paramiko.ServerInterface):
    """Simple SSH server for testing."""
    
    def __init__(self):
        self.event = threading.Event()
    
    def check_auth_password(self, username, password):
        """Accept any password for testing."""
        return paramiko.AUTH_SUCCESSFUL
    
    def check_auth_publickey(self, username, key):
        """Accept any public key for testing."""
        return paramiko.AUTH_SUCCESSFUL
    
    def check_channel_request(self, kind, chanid):
        """Allow session channels."""
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_channel_exec_request(self, channel, command):
        """Handle exec requests."""
        if command == b'echo SSH_TEST_SUCCESS':
            channel.send(b'SSH_TEST_SUCCESS\n')
            channel.send_exit_status(0)
            return True
        return False


def start_test_server(port=0):
    """Start a test SSH server and return the port it's listening on."""
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('127.0.0.1', port))
    server_socket.listen(1)
    
    # Get the actual port if we used 0
    actual_port = server_socket.getsockname()[1]
    
    # Generate a temporary host key
    host_key = paramiko.RSAKey.generate(2048)
    
    def server_thread():
        """Server thread function."""
        try:
            client_socket, addr = server_socket.accept()
            
            # Create transport
            transport = paramiko.Transport(client_socket)
            transport.add_server_key(host_key)
            
            # Start server
            server = DemoSSHServer()
            transport.start_server(server=server)
            
            # Wait for client to disconnect or timeout
            channel = transport.accept(20)
            if channel:
                channel.event.wait(10)
                channel.close()
            
            transport.close()
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            server_socket.close()
    
    # Start server in background thread
    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()
    
    # Give server time to start
    time.sleep(0.5)
    
    return actual_port, host_key


def _test_ssh_with_paramiko_client(host, port, username):
    """Test SSH connection using Paramiko client."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Try with key first
        ssh_dir = Path.home() / ".ssh"
        id_rsa = ssh_dir / "id_rsa"
        
        if id_rsa.exists():
            try:
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    key_filename=str(id_rsa),
                    timeout=5,
                    look_for_keys=False,
                    allow_agent=False
                )
            except Exception:
                # Fall back to password
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password='test',
                    timeout=5,
                    look_for_keys=False,
                    allow_agent=False
                )
        else:
            # Use password auth
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password='test',
                timeout=5,
                look_for_keys=False,
                allow_agent=False
            )
        
        # Execute test command
        stdin, stdout, stderr = client.exec_command('echo SSH_TEST_SUCCESS')
        output = stdout.read().decode().strip()
        
        return 'SSH_TEST_SUCCESS' in output
        
    except Exception as e:
        print(f"Connection error: {e}")
        return False
    finally:
        client.close()


def test_ssh_in_ci():
    """Test SSH connectivity using Paramiko test server."""
    
    print("Starting Paramiko test SSH server...")
    
    try:
        # Start test server
        port, host_key = start_test_server()
        print(f"Test server started on port {port}")
        
        # Get username
        username = os.environ.get("USER") or os.environ.get("USERNAME", "testuser")
        
        print(f"Testing SSH connection as {username}@127.0.0.1:{port}...")
        
        # Test connection
        success = _test_ssh_with_paramiko_client('127.0.0.1', port, username)
        
        if success:
            print("✓ SSH connection test successful!")
            return True
        else:
            print("✗ SSH test failed")
            return False
            
    except Exception as e:
        print(f"✗ SSH test error: {e}")
        return False


if __name__ == "__main__":
    success = test_ssh_in_ci()
    if not success:
        print("\nSSH test failed")
        sys.exit(1)
    sys.exit(0)

#!/usr/bin/env python3
"""
AI DevOps Automation - Deploy Script
Deploys application files to production server using SSH/SFTP
"""

import os
import sys
import paramiko
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
SERVER_HOST = os.getenv('SERVER_HOST')
SERVER_USER = os.getenv('SERVER_USER', 'root')
SERVER_PASSWORD = os.getenv('SERVER_PASSWORD')
SERVER_PORT = int(os.getenv('SERVER_PORT', '22'))

# Deployment configuration
CONTAINER_NAME = os.getenv('CONTAINER_NAME', 'web_container')
APP_PATH = os.getenv('APP_PATH', '/app')


def deploy_file(local_path, remote_path, container_path=None):
    """
    Deploy a file to the server and optionally copy to Docker container

    Args:
        local_path: Path to local file
        remote_path: Path on server (usually /tmp/)
        container_path: Path inside Docker container (optional)
    """

    if not all([SERVER_HOST, SERVER_PASSWORD]):
        print("❌ Error: SERVER_HOST and SERVER_PASSWORD must be set in .env file")
        sys.exit(1)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sftp = None

    try:
        print(f"🔌 Connecting to {SERVER_HOST}...")
        ssh.connect(
            SERVER_HOST,
            port=SERVER_PORT,
            username=SERVER_USER,
            password=SERVER_PASSWORD,
            timeout=10
        )
        sftp = ssh.open_sftp()
        print("✅ Connected")

        # Upload file
        print(f"📤 Uploading {local_path} to {remote_path}...")
        sftp.put(local_path, remote_path)
        print("✅ Upload complete")

        # Copy to container if specified
        if container_path:
            print(f"🐳 Copying to Docker container {CONTAINER_NAME}...")
            cmd = f"docker cp {remote_path} {CONTAINER_NAME}:{container_path}"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.read()
            print("✅ Copied to container")

            # Restart container
            print(f"🔄 Restarting container {CONTAINER_NAME}...")
            cmd = f"docker compose restart {CONTAINER_NAME}"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.read()
            print("✅ Container restarted")

        print("\n🎉 Deployment successful!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if sftp:
            sftp.close()
        ssh.close()


if __name__ == '__main__':
    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python deploy.py <local_file> [container_path]")
        print("Example: python deploy.py app.py /app/app.py")
        sys.exit(1)

    local_file = sys.argv[1]
    container_path = sys.argv[2] if len(sys.argv) > 2 else None

    # Use /tmp/ on server
    remote_tmp = f"/tmp/{os.path.basename(local_file)}"

    deploy_file(local_file, remote_tmp, container_path)

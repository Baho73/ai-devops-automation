#!/usr/bin/env python3
"""
AI DevOps Automation - Log Checker
Retrieves and analyzes Docker container logs
"""

import os
import sys
import paramiko
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SERVER_HOST = os.getenv('SERVER_HOST')
SERVER_USER = os.getenv('SERVER_USER', 'root')
SERVER_PASSWORD = os.getenv('SERVER_PASSWORD')
SERVER_PORT = int(os.getenv('SERVER_PORT', '22'))
CONTAINER_NAME = os.getenv('CONTAINER_NAME', 'web_container')


def check_logs(container_name=None, lines=50):
    """
    Retrieve and display Docker container logs

    Args:
        container_name: Name of Docker container
        lines: Number of lines to retrieve
    """

    if not all([SERVER_HOST, SERVER_PASSWORD]):
        print("❌ Error: SERVER_HOST and SERVER_PASSWORD must be set in .env file")
        sys.exit(1)

    if not container_name:
        container_name = CONTAINER_NAME

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"🔌 Connecting to {SERVER_HOST}...")
        ssh.connect(
            SERVER_HOST,
            port=SERVER_PORT,
            username=SERVER_USER,
            password=SERVER_PASSWORD,
            timeout=10
        )
        print("✅ Connected\n")

        # Get container logs
        cmd = f"docker logs {container_name} --tail {lines}"
        stdin, stdout, stderr = ssh.exec_command(cmd)

        logs = stdout.read().decode()
        errors = stderr.read().decode()

        print(f"=== 📋 LOGS: {container_name} (last {lines} lines) ===")
        print(logs)

        if errors:
            print(f"\n=== ⚠️ STDERR ===")
            print(errors)

        # Analyze for errors
        error_keywords = ['Error', 'Exception', 'Traceback', 'FAILED', 'CRITICAL', 'fatal']
        has_errors = any(keyword in logs or keyword in errors for keyword in error_keywords)

        if has_errors:
            print("\n⚠️ WARNING: Errors detected in logs!")
            error_lines = [
                line for line in (logs + errors).split('\n')
                if any(kw in line for kw in error_keywords)
            ]
            print("\n🔍 Error lines:")
            for line in error_lines[:10]:  # Show first 10 error lines
                print(f"  {line}")
        else:
            print("\n✅ No errors detected")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        ssh.close()


if __name__ == '__main__':
    container = sys.argv[1] if len(sys.argv) > 1 else None
    lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    check_logs(container, lines)

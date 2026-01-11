"""
CLI Tools - Command-line tool execution for Kaedra Orchestrator

Provides Kaedra with the same CLI capabilities as Claude:
- Shell command execution
- File operations
- Git operations
- Process management
- System diagnostics
"""

import subprocess
import os
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


class CLITools:
    """Command-line interface tools for Kaedra orchestrator."""

    def __init__(self, working_dir: str = None):
        """
        Initialize CLI tools.

        Args:
            working_dir: Default working directory for commands
        """
        self.working_dir = working_dir or os.getcwd()
        self.command_history: List[Dict] = []

    def run_command(
        self,
        command: str,
        timeout: int = 30,
        capture_output: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a shell command.

        Args:
            command: Shell command to execute
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr

        Returns:
            Dict with status, stdout, stderr, returncode
        """
        result = {
            "command": command,
            "timestamp": datetime.now().isoformat(),
            "working_dir": self.working_dir,
            "status": "success",
            "stdout": "",
            "stderr": "",
            "returncode": 0
        }

        try:
            process = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )

            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["returncode"] = process.returncode

            if process.returncode != 0:
                result["status"] = "error"

        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["stderr"] = f"Command timed out after {timeout} seconds"
            result["returncode"] = -1

        except Exception as e:
            result["status"] = "error"
            result["stderr"] = str(e)
            result["returncode"] = -1

        # Log command
        self.command_history.append(result)

        return result

    # File Operations
    def read_file(self, filepath: str) -> Dict[str, Any]:
        """Read file contents."""
        return self.run_command(f'cat "{filepath}"')

    def write_file(self, filepath: str, content: str) -> Dict[str, Any]:
        """Write content to file."""
        # Escape content for shell
        escaped = content.replace("'", "'\\''")
        return self.run_command(f"echo '{escaped}' > '{filepath}'")

    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """List directory contents."""
        return self.run_command(f'ls -la "{path}"')

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create directory."""
        return self.run_command(f'mkdir -p "{path}"')

    def remove_file(self, path: str) -> Dict[str, Any]:
        """Remove file or directory."""
        return self.run_command(f'rm -rf "{path}"')

    def copy_file(self, source: str, dest: str) -> Dict[str, Any]:
        """Copy file or directory."""
        return self.run_command(f'cp -r "{source}" "{dest}"')

    def move_file(self, source: str, dest: str) -> Dict[str, Any]:
        """Move/rename file."""
        return self.run_command(f'mv "{source}" "{dest}"')

    # Git Operations
    def git_status(self) -> Dict[str, Any]:
        """Get git status."""
        return self.run_command("git status")

    def git_diff(self) -> Dict[str, Any]:
        """Get git diff."""
        return self.run_command("git diff")

    def git_log(self, limit: int = 10) -> Dict[str, Any]:
        """Get git log."""
        return self.run_command(f"git log --oneline -n {limit}")

    def git_add(self, files: str = ".") -> Dict[str, Any]:
        """Stage files for commit."""
        return self.run_command(f'git add "{files}"')

    def git_commit(self, message: str) -> Dict[str, Any]:
        """Create git commit."""
        return self.run_command(f'git commit -m "{message}"')

    def git_push(self) -> Dict[str, Any]:
        """Push to remote."""
        return self.run_command("git push")

    def git_pull(self) -> Dict[str, Any]:
        """Pull from remote."""
        return self.run_command("git pull")

    # Process Management
    def list_processes(self) -> Dict[str, Any]:
        """List running processes."""
        return self.run_command("ps aux")

    def kill_process(self, pid: int) -> Dict[str, Any]:
        """Kill process by PID."""
        return self.run_command(f"kill {pid}")

    # System Diagnostics
    def disk_usage(self, path: str = ".") -> Dict[str, Any]:
        """Check disk usage."""
        return self.run_command(f'du -sh "{path}"')

    def system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return self.run_command("uname -a")

    def memory_usage(self) -> Dict[str, Any]:
        """Check memory usage."""
        return self.run_command("free -h")

    # Search Operations
    def find_files(self, pattern: str, path: str = ".") -> Dict[str, Any]:
        """Find files matching pattern."""
        return self.run_command(f'find "{path}" -name "{pattern}"')

    def grep_files(self, pattern: str, path: str = ".", file_pattern: str = "*") -> Dict[str, Any]:
        """Search for pattern in files."""
        return self.run_command(f'grep -r "{pattern}" "{path}" --include="{file_pattern}"')

    # Package Management
    def pip_install(self, package: str) -> Dict[str, Any]:
        """Install Python package."""
        return self.run_command(f"pip install {package}")

    def npm_install(self, package: str = "") -> Dict[str, Any]:
        """Install npm package."""
        cmd = "npm install" if not package else f"npm install {package}"
        return self.run_command(cmd)

    # Utility
    def change_directory(self, path: str) -> Dict[str, Any]:
        """Change working directory."""
        try:
            os.chdir(path)
            self.working_dir = os.getcwd()
            return {
                "status": "success",
                "working_dir": self.working_dir,
                "message": f"Changed to {self.working_dir}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def get_working_directory(self) -> str:
        """Get current working directory."""
        return self.working_dir

    def get_command_history(self, limit: int = 10) -> List[Dict]:
        """Get recent command history."""
        return self.command_history[-limit:]


# Singleton instance for orchestrator use
cli_tools = CLITools()


if __name__ == "__main__":
    # Test CLI tools
    print("🔧 CLI Tools Test\n")

    tools = CLITools()

    # Test file operations
    print("Testing file operations...")
    result = tools.list_directory(".")
    print(f"  ls result: {result['status']}")

    # Test git operations
    print("\nTesting git operations...")
    result = tools.git_status()
    print(f"  git status: {result['status']}")

    # Show command history
    print("\nCommand History:")
    for cmd in tools.get_command_history():
        print(f"  [{cmd['status']}] {cmd['command']}")

"""
Code Execution - Multi-Language Code Execution for Kaedra Orchestrator

Executes code in various languages and frameworks from the official tech stack.
Supports: TypeScript, JavaScript, React, Next.js, Kotlin, Python, and more.
"""

import os
import subprocess
import json
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path


class CodeExecutor:
    """Execute code in various languages and frameworks."""

    def __init__(self, working_dir: str = None):
        """
        Initialize code executor.

        Args:
            working_dir: Working directory for code execution
        """
        self.working_dir = working_dir or os.getcwd()
        self.execution_history: List[Dict] = []

    def execute_typescript(
        self,
        code: str,
        filename: str = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute TypeScript code using tsx/ts-node.

        Args:
            code: TypeScript code to execute
            filename: Optional filename (for context)
            timeout: Execution timeout in seconds

        Returns:
            Execution result
        """
        result = {
            "language": "typescript",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "stdout": "",
            "stderr": "",
            "returncode": 0
        }

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.ts',
                delete=False,
                dir=self.working_dir
            ) as f:
                f.write(code)
                temp_file = f.name

            # Execute with tsx (faster than ts-node)
            process = subprocess.run(
                ['npx', 'tsx', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir
            )

            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["returncode"] = process.returncode

            if process.returncode != 0:
                result["status"] = "error"

        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["stderr"] = f"Execution timed out after {timeout}s"
            result["returncode"] = -1

        except Exception as e:
            result["status"] = "error"
            result["stderr"] = str(e)
            result["returncode"] = -1

        finally:
            # Cleanup temp file
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass

        self.execution_history.append(result)
        return result

    def execute_javascript(
        self,
        code: str,
        filename: str = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute JavaScript code using Node.js.

        Args:
            code: JavaScript code to execute
            filename: Optional filename
            timeout: Execution timeout

        Returns:
            Execution result
        """
        result = {
            "language": "javascript",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "stdout": "",
            "stderr": "",
            "returncode": 0
        }

        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.js',
                delete=False,
                dir=self.working_dir
            ) as f:
                f.write(code)
                temp_file = f.name

            # Execute with node
            process = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir
            )

            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["returncode"] = process.returncode

            if process.returncode != 0:
                result["status"] = "error"

        except Exception as e:
            result["status"] = "error"
            result["stderr"] = str(e)
            result["returncode"] = -1

        finally:
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass

        self.execution_history.append(result)
        return result

    def execute_python(
        self,
        code: str,
        filename: str = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute Python code.

        Args:
            code: Python code to execute
            filename: Optional filename
            timeout: Execution timeout

        Returns:
            Execution result
        """
        result = {
            "language": "python",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "stdout": "",
            "stderr": "",
            "returncode": 0
        }

        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                dir=self.working_dir
            ) as f:
                f.write(code)
                temp_file = f.name

            process = subprocess.run(
                ['python3', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir
            )

            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["returncode"] = process.returncode

            if process.returncode != 0:
                result["status"] = "error"

        except Exception as e:
            result["status"] = "error"
            result["stderr"] = str(e)
            result["returncode"] = -1

        finally:
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass

        self.execution_history.append(result)
        return result

    def execute_kotlin(
        self,
        code: str,
        filename: str = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute Kotlin code using kotlinc.

        Args:
            code: Kotlin code to execute
            filename: Optional filename
            timeout: Execution timeout

        Returns:
            Execution result
        """
        result = {
            "language": "kotlin",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "stdout": "",
            "stderr": "",
            "returncode": 0
        }

        try:
            # Create temp .kt file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.kt',
                delete=False,
                dir=self.working_dir
            ) as f:
                f.write(code)
                temp_file = f.name

            # Compile Kotlin
            compile_process = subprocess.run(
                ['kotlinc', temp_file, '-include-runtime', '-d', f'{temp_file}.jar'],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir
            )

            if compile_process.returncode != 0:
                result["status"] = "error"
                result["stderr"] = f"Compilation failed:\n{compile_process.stderr}"
                result["returncode"] = compile_process.returncode
            else:
                # Execute compiled jar
                run_process = subprocess.run(
                    ['java', '-jar', f'{temp_file}.jar'],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.working_dir
                )

                result["stdout"] = run_process.stdout
                result["stderr"] = run_process.stderr
                result["returncode"] = run_process.returncode

                if run_process.returncode != 0:
                    result["status"] = "error"

        except Exception as e:
            result["status"] = "error"
            result["stderr"] = str(e)
            result["returncode"] = -1

        finally:
            # Cleanup
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                    os.unlink(f'{temp_file}.jar')
                except:
                    pass

        self.execution_history.append(result)
        return result

    def create_nextjs_project(
        self,
        project_name: str,
        path: str = None
    ) -> Dict[str, Any]:
        """
        Create a new Next.js 16.0.3 project with official tech stack.

        Args:
            project_name: Name of the project
            path: Path to create project (defaults to working_dir)

        Returns:
            Creation result
        """
        target_path = path or self.working_dir

        result = {
            "action": "create_nextjs_project",
            "project_name": project_name,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "path": os.path.join(target_path, project_name)
        }

        try:
            # Create Next.js project with exact version
            process = subprocess.run(
                [
                    'npx',
                    'create-next-app@16.0.3',
                    project_name,
                    '--typescript',
                    '--tailwind',
                    '--app',
                    '--no-git'
                ],
                capture_output=True,
                text=True,
                cwd=target_path,
                timeout=300  # 5 minutes for installation
            )

            if process.returncode != 0:
                result["status"] = "error"
                result["error"] = process.stderr
                return result

            # Initialize Shadcn UI
            project_path = os.path.join(target_path, project_name)

            shadcn_process = subprocess.run(
                ['npx', 'shadcn@latest', 'init', '-y'],
                capture_output=True,
                text=True,
                cwd=project_path,
                timeout=60
            )

            # Install exact React versions
            react_install = subprocess.run(
                ['npm', 'install', 'react@19.2.0', 'react-dom@19.2.0'],
                capture_output=True,
                text=True,
                cwd=project_path,
                timeout=120
            )

            result["output"] = {
                "nextjs_setup": process.stdout,
                "shadcn_setup": shadcn_process.stdout,
                "react_install": react_install.stdout
            }

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def create_expo_project(
        self,
        project_name: str,
        path: str = None
    ) -> Dict[str, Any]:
        """
        Create a new Expo project.

        Args:
            project_name: Name of the project
            path: Path to create project

        Returns:
            Creation result
        """
        target_path = path or self.working_dir

        result = {
            "action": "create_expo_project",
            "project_name": project_name,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "path": os.path.join(target_path, project_name)
        }

        try:
            process = subprocess.run(
                ['npx', 'create-expo-app@latest', project_name, '--template', 'blank-typescript'],
                capture_output=True,
                text=True,
                cwd=target_path,
                timeout=300
            )

            result["output"] = process.stdout

            if process.returncode != 0:
                result["status"] = "error"
                result["error"] = process.stderr

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def run_npm_script(
        self,
        script: str,
        project_path: str = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Run npm script in a project.

        Args:
            script: npm script to run (e.g., 'dev', 'build', 'test')
            project_path: Path to project
            timeout: Execution timeout

        Returns:
            Execution result
        """
        path = project_path or self.working_dir

        result = {
            "action": "npm_script",
            "script": script,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }

        try:
            process = subprocess.run(
                ['npm', 'run', script],
                capture_output=True,
                text=True,
                cwd=path,
                timeout=timeout
            )

            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["returncode"] = process.returncode

            if process.returncode != 0:
                result["status"] = "error"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def get_execution_history(self, limit: int = 10) -> List[Dict]:
        """Get recent execution history."""
        return self.execution_history[-limit:]


# Singleton for orchestrator use
code_executor = CodeExecutor()


if __name__ == "__main__":
    # Test code execution
    print("💻 Code Execution Test\n")

    executor = CodeExecutor()

    # Test TypeScript
    print("Testing TypeScript execution...")
    ts_code = """
console.log("Hello from TypeScript!");
const version: string = "19.2";
console.log(`React version: ${version}`);
"""
    result = executor.execute_typescript(ts_code)
    print(f"  Status: {result['status']}")
    print(f"  Output: {result['stdout']}")

    # Test Python
    print("\nTesting Python execution...")
    py_code = """
print("Hello from Python!")
print("Tech Stack: Next.js 16.0.3")
"""
    result = executor.execute_python(py_code)
    print(f"  Status: {result['status']}")
    print(f"  Output: {result['stdout']}")

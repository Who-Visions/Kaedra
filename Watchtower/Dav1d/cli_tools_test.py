#!/usr/bin/env python3
"""
Test CLI tool integration with DAV1D
"""
import sys
sys.path.insert(0, '.')

from dav1d import (
    execute_shell_command,
    list_files,
    read_file_content,
    write_file_content,
    CLI_TOOLS,
    CLI_TOOL_FUNCTIONS
)

print("="*80)
print("🔧 DAV1D CLI TOOLS TEST")
print("="*80)

print("\n1. Testing execute_shell_command...")
result = execute_shell_command("dir", timeout=10)
print(f"   Success: {result['success']}")

print("\n2. Testing list_files...")
result = list_files(".", "*.md")
print(f"   Found {result.get('count', 0)} markdown files")

print("\n3. Testing write_file_content...")
result = write_file_content("test_cli.txt", "CLI tools are working!")
print(f"   Success: {result['success']}")

print("\n4. Testing read_file_content...")
result = read_file_content("test_cli.txt")
print(f"   Content: {result.get('content', 'ERROR')[:50]}")

print("\n5. Checking CLI_TOOLS declaration...")
print(f"   Registered tools: {len(CLI_TOOLS)}")
for tool in CLI_TOOLS:
    print(f"   - {tool['name']}")

print("\n6. Checking function mapping...")
print(f"   Mapped functions: {len(CLI_TOOL_FUNCTIONS)}")
for name in CLI_TOOL_FUNCTIONS:
    print(f"   - {name}")

print("\n"+"="*80)
print("✅ CLI TOOLS INTEGRATION TEST COMPLETE")
print("="*80)
print("\n💡 Now restart DAV1D and try:")
print("   • 'Check git status'")
print("   • 'Show me all Python files'")
print("   • 'Create a file called notes.txt'")
print()

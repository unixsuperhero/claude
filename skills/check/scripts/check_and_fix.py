#!/usr/bin/env python3
"""
Orchestrator script to detect changed files and run appropriate lint/test commands.
Handles the complex monorepo structure with different apps and file types.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Configuration for an app in the monorepo."""
    name: str
    rel_path: str
    js_commands: List[str]
    ruby_commands: List[str]
    js_deps_check: str = "yarn"
    ruby_deps_check: str = "bundle install"


# App configurations
APPS = [
    AppConfig(
        name="partners",
        rel_path="partners/partners",
        js_commands=["yarn lint", "yarn test"],
        ruby_commands=["bundle exec rubocop", "bundle exec rspec"],
    ),
    AppConfig(
        name="customers-backend",
        rel_path="customers/customers-backend",
        js_commands=[],
        ruby_commands=["bundle exec rubocop", "bundle exec rspec"],
    ),
    AppConfig(
        name="ipp",
        rel_path="retailer-tools/retailer-platform-web-workspace",
        js_commands=["yarn lint", "yarn test"],
        ruby_commands=["bundle exec rubocop", "bundle exec rspec"],
    ),
]

# File extension mappings
JS_TS_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
RUBY_EXTS = {".rb", ".rake", ".ru"}


def run_command(cmd: str, cwd: Path, description: str) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    print(f"\n{'='*60}")
    print(f"Running: {cmd}")
    print(f"In: {cwd}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        output = result.stdout + result.stderr
        print(output)

        success = result.returncode == 0
        if success:
            print(f"✅ {description} passed")
        else:
            print(f"❌ {description} failed")

        return success, output

    except subprocess.TimeoutExpired:
        error_msg = f"⏱️  Command timed out after 5 minutes: {cmd}"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"⚠️  Error running command: {e}"
        print(error_msg)
        return False, error_msg


def get_git_root() -> Path:
    """Get the git repository root directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        print("❌ Not in a git repository")
        sys.exit(1)


def get_changed_files() -> Set[str]:
    """Get all changed files (staged and unstaged)."""
    try:
        # Get staged files
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "origin/master"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip().split("\n")

        # Get unstaged files
        unstaged = subprocess.run(
            ["git", "diff", "--name-only", "origin/master"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip().split("\n")

        # Get untracked files
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip().split("\n")

        # Combine all, filter empty strings
        all_files = set(f for f in staged + unstaged + untracked if f)

        return all_files

    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting changed files: {e}")
        sys.exit(1)


def categorize_files(files: Set[str], git_root: Path) -> Dict[str, Dict[str, List[str]]]:
    """
    Categorize files by app and file type.
    Returns: {app_name: {file_type: [files]}}
    """
    categorized = {}

    for app in APPS:
        app_files = {
            "js_ts": [],
            "ruby": [],
        }

        for file in files:
            # Check if file is in this app's directory
            if file.startswith(app.rel_path):
                file_path = Path(file)
                ext = file_path.suffix.lower()

                if ext in JS_TS_EXTS:
                    app_files["js_ts"].append(file)
                elif ext in RUBY_EXTS:
                    app_files["ruby"].append(file)

        # Only include app if it has changed files
        if app_files["js_ts"] or app_files["ruby"]:
            categorized[app.name] = app_files

    return categorized


def check_dependencies_installed(app_dir: Path, file_type: str) -> bool:
    """Check if dependencies are installed for given file type."""
    if file_type == "js_ts":
        # Check if node_modules exists
        return (app_dir / "node_modules").exists()
    elif file_type == "ruby":
        # Check if vendor/bundle exists or .bundle/config exists
        return (app_dir / "vendor" / "bundle").exists() or (app_dir / ".bundle" / "config").exists()
    return True


def process_app(app: AppConfig, file_types: Dict[str, List[str]], git_root: Path, auto_fix: bool = True) -> bool:
    """Process an app: install deps if needed, then run lint/test commands."""
    app_dir = git_root / app.rel_path

    print(f"\n{'#'*60}")
    print(f"# Processing {app.name.upper()}")
    print(f"# Location: {app_dir}")
    print(f"{'#'*60}")

    all_success = True

    # Helper function to convert git-root-relative paths to app-relative paths
    def make_app_relative(files: List[str]) -> List[str]:
        """Strip the app.rel_path prefix from file paths."""
        app_prefix = app.rel_path + "/"
        return [f.removeprefix(app_prefix) for f in files]

    # Process JS/TS files
    if file_types["js_ts"] and app.js_commands:
        print(f"\n📦 Found {len(file_types['js_ts'])} JS/TS file(s) in {app.name}")

        # Check and install dependencies if needed
        if not check_dependencies_installed(app_dir, "js_ts"):
            print("📥 Installing JS dependencies...")
            success, _ = run_command(app.js_deps_check, app_dir, "Dependency installation")
            if not success:
                print(f"⚠️  Warning: Dependency installation had issues, continuing anyway...")

        # Run JS commands
        for cmd in app.js_commands:
            # Add --fix flag for lint commands if auto_fix is enabled
            if auto_fix and "lint" in cmd and "--fix" not in cmd:
                cmd = f"{cmd} --fix"

            success, _ = run_command(cmd, app_dir, cmd)
            if not success:
                all_success = False

    # Process Ruby files
    if file_types["ruby"] and app.ruby_commands:
        print(f"\n💎 Found {len(file_types['ruby'])} Ruby file(s) in {app.name}")

        # Check and install dependencies if needed
        if not check_dependencies_installed(app_dir, "ruby"):
            print("📥 Installing Ruby dependencies...")
            success, _ = run_command(app.ruby_deps_check, app_dir, "Dependency installation")
            if not success:
                print(f"⚠️  Warning: Dependency installation had issues, continuing anyway...")

        # Run Ruby commands
        for cmd in app.ruby_commands:
            # Handle rubocop - pass all changed Ruby files
            if "rubocop" in cmd:
                # Add -a flag if auto_fix is enabled
                if auto_fix and "-a" not in cmd and "-A" not in cmd:
                    cmd = f"{cmd} -a"

                # Add the changed files (converted to app-relative paths)
                app_relative_files = make_app_relative(file_types["ruby"])
                files_str = " ".join(app_relative_files)
                cmd = f"{cmd} {files_str}"

                success, _ = run_command(cmd, app_dir, cmd)
                if not success:
                    all_success = False

            # Handle rspec - only run spec files
            elif "rspec" in cmd:
                # Filter to only _spec.rb files in spec/ directories
                spec_files = [f for f in file_types["ruby"] if f.endswith("_spec.rb") and "/spec/" in f]

                if spec_files:
                    # Convert to app-relative paths
                    app_relative_files = make_app_relative(spec_files)
                    files_str = " ".join(app_relative_files)
                    cmd = f"{cmd} {files_str}"

                    success, _ = run_command(cmd, app_dir, cmd)
                    if not success:
                        all_success = False
                else:
                    print(f"ℹ️  No spec files changed, skipping rspec")

            # Handle other Ruby commands (if any)
            else:
                success, _ = run_command(cmd, app_dir, cmd)
                if not success:
                    all_success = False

    # Special case: IPP with bento lint
    if app.name == "ipp" and (file_types["js_ts"] or file_types["ruby"]):
        print(f"\n🍱 Running bento lint for IPP...")
        success, _ = run_command("bento lint", app_dir, "Bento lint")
        if not success:
            all_success = False

    return all_success


def main():
    """Main orchestrator function."""
    print("🔍 Checking for changed files and running lint/test commands...")

    # Get git root
    git_root = get_git_root()
    print(f"📂 Git root: {git_root}")

    # Get changed files
    changed_files = get_changed_files()

    if not changed_files:
        print("✅ No changed files detected")
        return 0

    print(f"\n📝 Found {len(changed_files)} changed file(s)")

    # Categorize files by app and type
    categorized = categorize_files(changed_files, git_root)

    if not categorized:
        print("ℹ️  No changed files in tracked app directories")
        return 0

    print(f"\n📊 Changes detected in {len(categorized)} app(s):")
    for app_name, file_types in categorized.items():
        js_count = len(file_types["js_ts"])
        ruby_count = len(file_types["ruby"])
        print(f"  • {app_name}: {js_count} JS/TS, {ruby_count} Ruby")

    # Process each app
    all_success = True
    for app_name, file_types in categorized.items():
        app_config = next(a for a in APPS if a.name == app_name)
        success = process_app(app_config, file_types, git_root, auto_fix=True)
        if not success:
            all_success = False

    # Final summary
    print(f"\n{'='*60}")
    if all_success:
        print("✅ All checks passed!")
        return 0
    else:
        print("❌ Some checks failed - review output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Read selected project manifests and optional installed-package names."""

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tomllib


SKIP_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "vendor",
    "target", "dist", "build", ".next", ".cache", ".terraform", "__pycache__",
    "Pods", ".tox", ".yarn", ".pnpm-store", "coverage",
}
MANIFESTS = {
    "package.json", "pyproject.toml", "requirements.txt", "Pipfile", "setup.cfg",
    "Cargo.toml", "go.mod", "Gemfile", "composer.json", "CMakeLists.txt",
    "Makefile", "Dockerfile", "compose.yaml", "compose.yml", "docker-compose.yml",
    "docker-compose.yaml", "Brewfile", "flake.nix", "shell.nix", "devenv.nix",
    ".tool-versions", ".nvmrc", ".node-version", ".python-version", "rust-toolchain.toml",
}
LOCK_HINTS = {"pnpm-lock.yaml": "pnpm", "yarn.lock": "yarn", "bun.lock": "bun",
              "bun.lockb": "bun", "uv.lock": "uv", "poetry.lock": "poetry"}
# Small leads, deliberately not a universal name converter. Verify the pin later.
TOOLS = {
    "git": ("git", "user"), "rg": ("ripgrep", "user"), "fd": ("fd", "user"),
    "nvim": ("neovim", "user"), "vim": ("vim", "user"), "jq": ("jq", "user"),
    "node": ("nodejs", "devShell"), "python3": ("python3", "devShell"),
    "go": ("go", "devShell"), "cargo": ("cargo", "devShell"),
    "rustc": ("rustc", "devShell"), "ruby": ("ruby", "devShell"),
    "php": ("php", "devShell"), "composer": ("phpPackages.composer", "devShell"),
    "cmake": ("cmake", "devShell"), "make": ("gnumake", "devShell"),
    "pkg-config": ("pkg-config", "devShell"), "cc": ("stdenv.cc", "devShell"),
    "pnpm": ("pnpm", "devShell"), "yarn": ("yarn", "devShell"),
    "bun": ("bun", "devShell"), "uv": ("uv", "devShell"),
    "poetry": ("poetry", "devShell"), "docker": ("docker", "manual"),
    "podman": ("podman", "manual"), "psql": ("postgresql", "manual"),
}
FORMULAE = {"ripgrep": "rg", "neovim": "nvim", "python": "python3",
            "nodejs": "node", "rust": "rustc", "gcc": "cc"}


class Inventory:
    def __init__(self):
        self.data = {
            "schema_version": 1,
            "host": {"os": platform.system(), "architecture": platform.machine()},
            "roots": [], "projects": [], "candidates": [], "installed_packages": [],
            "unmapped_packages": [], "warnings": [],
            "limits": {},
        }
        self.candidates = {}

    def suggest(self, tool, source, confidence="medium", version=None):
        attr, scope = TOOLS[tool]
        key = (attr, scope)
        if key not in self.candidates:
            self.candidates[key] = {
                "nix_attribute": attr, "scope": scope, "verified": False,
                "evidence": [],
            }
        evidence = {"source": source, "confidence": confidence}
        if version:
            evidence["declared_version"] = str(version)
        if evidence not in self.candidates[key]["evidence"]:
            self.candidates[key]["evidence"].append(evidence)

    def package(self, name, source, kind):
        name = name.strip()
        if not name:
            return
        item = {"name": name, "source": source, "kind": kind}
        self.data["installed_packages"].append(item)
        base = name.rsplit("/", 1)[-1].split("@")[0]
        tool = FORMULAE.get(base, base)
        # A cask may share a tool name but requires independent platform review.
        if kind != "cask" and tool in TOOLS:
            self.suggest(tool, f"{source}: {name}", "low")
        else:
            self.data["unmapped_packages"].append(item)

    def inspect(self, path, text):
        source = str(path)
        name = path.name
        self.data["projects"].append({"manifest": source})
        if name in LOCK_HINTS:
            self.suggest(LOCK_HINTS[name], source, "high")
        elif name == "package.json":
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError("expected a JSON object")
            engines = value.get("engines", {})
            version = engines.get("node") if isinstance(engines, dict) else None
            self.suggest("node", source, "high", version)
            manager = value.get("packageManager", "")
            if isinstance(manager, str):
                tool, _, version = manager.partition("@")
                if tool in {"pnpm", "yarn", "bun"}:
                    self.suggest(tool, source, "high", version)
        elif name == "pyproject.toml":
            value = tomllib.loads(text)
            project = value.get("project", {})
            version = project.get("requires-python") if isinstance(project, dict) else None
            self.suggest("python3", source, "high", version)
            tool = value.get("tool", {})
            if isinstance(tool, dict):
                for manager in ("poetry", "uv"):
                    if manager in tool:
                        self.suggest(manager, source, "high")
        elif name in {"requirements.txt", "Pipfile", "setup.cfg"}:
            self.suggest("python3", source, "high")
        elif name in {"Cargo.toml", "rust-toolchain.toml"}:
            value = tomllib.loads(text)
            toolchain = value.get("toolchain", {})
            version = toolchain.get("channel") if isinstance(toolchain, dict) else None
            self.suggest("cargo", source, "high", version)
            self.suggest("rustc", source, "high", version)
        elif name == "go.mod":
            match = re.search(r"(?m)^go\s+([^\s]+)", text)
            self.suggest("go", source, "high", match[1] if match else None)
        elif name == "Gemfile":
            self.suggest("ruby", source, "high")
        elif name == "composer.json":
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError("expected a JSON object")
            requirements = value.get("require", {})
            version = requirements.get("php") if isinstance(requirements, dict) else None
            self.suggest("php", source, "high", version)
            self.suggest("composer", source, "high")
        elif name == "CMakeLists.txt":
            self.suggest("cmake", source, "high")
            self.suggest("cc", source, "medium")
            if "pkg_check_modules" in text or "PkgConfig" in text:
                self.suggest("pkg-config", source, "high")
        elif name == "Makefile":
            self.suggest("make", source, "high")
        elif name == "Dockerfile" or "compose" in name:
            self.suggest("docker", source, "medium")
        elif name == "Brewfile":
            for kind, formula in re.findall(r'(?m)^\s*(brew|cask)\s+["\x27]([^"\x27]+)["\x27]', text):
                self.package(formula, source, "cask" if kind == "cask" else "formula")
        elif name in {".nvmrc", ".node-version", ".python-version"}:
            self.suggest("python3" if name == ".python-version" else "node", source,
                         "high", text.strip()[:120])
        elif name == ".tool-versions":
            for line in text.splitlines():
                fields = line.split()
                if len(fields) < 2 or fields[0].startswith("#"):
                    continue
                tool = {"nodejs": "node", "python": "python3", "golang": "go"}.get(fields[0], fields[0])
                if tool in TOOLS:
                    self.suggest(tool, source, "high", " ".join(fields[1:])[:120])
        # Nix files are recorded as existing environments, never evaluated.

    def finish(self):
        self.data["candidates"] = sorted(self.candidates.values(), key=lambda x: (x["scope"], x["nix_attribute"]))
        return self.data


def scan_root(inventory, root, max_depth, remaining, max_bytes):
    if root.is_symlink():
        raise ValueError(f"Repository root is a symlink: {root}")
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Repository directory does not exist: {root}")
    inventory.data["roots"].append(str(root))

    def walk_error(exc):
        inventory.data["warnings"].append(f"Cannot traverse {exc.filename}: {exc.strerror}")

    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        current = Path(directory)
        depth = len(current.relative_to(root).parts)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (current / d).is_symlink())
        if depth >= max_depth:
            if dirs:
                inventory.data["warnings"].append(f"Depth limit reached at {current}; nested directories skipped")
            dirs[:] = []
        for name in sorted(files):
            if name not in MANIFESTS and name not in LOCK_HINTS:
                continue
            if remaining[0] == 0:
                inventory.data["warnings"].append(f"Manifest limit reached; remaining files in {root} skipped")
                return
            remaining[0] -= 1
            path = current / name
            try:
                if path.is_symlink() or not path.is_file():
                    inventory.data["warnings"].append(f"Skipped non-regular file or symlink: {path}")
                    continue
                # Lockfiles need only existence evidence; never read large/binary locks.
                if name in LOCK_HINTS:
                    inventory.inspect(path, "")
                    continue
                if path.stat().st_size > max_bytes:
                    inventory.data["warnings"].append(f"Oversized manifest skipped: {path}")
                    continue
                # Limit the read as well, in case a file grows after stat.
                with path.open("rb") as handle:
                    content = handle.read(max_bytes + 1)
                if len(content) > max_bytes:
                    inventory.data["warnings"].append(f"Oversized manifest skipped: {path}")
                    continue
                inventory.inspect(path, content.decode("utf-8"))
            except (OSError, ValueError, TypeError) as exc:
                # Parser errors may echo input. Report only their class, not file contents.
                inventory.data["warnings"].append(f"Could not inspect {path}: {type(exc).__name__}")


def host_packages(inventory):
    commands = []
    if shutil.which("brew"):
        commands += [("brew", "formula", ["brew", "list", "--formula", "-1"]),
                     ("brew", "cask", ["brew", "list", "--cask", "-1"])]
    if platform.system() == "Linux":
        if shutil.which("dpkg-query"):
            commands.append(("dpkg", "package", ["dpkg-query", "-W", "-f=${binary:Package}\n"]))
        elif shutil.which("pacman"):
            commands.append(("pacman", "package", ["pacman", "-Qq"]))
        elif shutil.which("rpm"):
            commands.append(("rpm", "package", ["rpm", "-qa", "--queryformat", "%{NAME}\n"]))
    env = os.environ.copy()
    env.update({"HOMEBREW_NO_AUTO_UPDATE": "1", "HOMEBREW_NO_ANALYTICS": "1", "LC_ALL": "C"})
    for manager, kind, command in commands:
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True,
                                    timeout=20, env=env)
            names = result.stdout.splitlines()
            if len(names) > 10000:
                inventory.data["warnings"].append(f"{manager} inventory limited to 10000 names")
            for name in names[:10000]:
                inventory.package(name, f"host:{manager}", kind)
        except (OSError, subprocess.SubprocessError) as exc:
            inventory.data["warnings"].append(f"Could not query {manager}: {type(exc).__name__}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", action="append", type=Path, default=[], help="Repository root; repeatable")
    parser.add_argument("--host-packages", action="store_true", help="Query installed package names (read-only)")
    parser.add_argument("--max-depth", type=int, default=5)
    parser.add_argument("--max-files", type=int, default=2000, help="Maximum selected manifests across all roots")
    parser.add_argument("--max-bytes", type=int, default=524288, help="Maximum bytes per text manifest")
    args = parser.parse_args(argv)
    if args.max_depth < 0 or args.max_files < 1 or args.max_bytes < 1:
        parser.error("depth must be nonnegative; file and byte limits must be positive")
    inventory = Inventory()
    inventory.data["limits"] = {"max_depth": args.max_depth, "max_files": args.max_files, "max_bytes": args.max_bytes}
    # Availability checks do not invoke tool binaries or version commands.
    for tool in TOOLS:
        location = shutil.which(tool)
        if location:
            inventory.suggest(tool, f"host:PATH:{location}", "low")
    remaining = [args.max_files]
    roots = set()
    for root in args.repo:
        root = root.expanduser()
        # Reject a symlink root before resolve, including a symlinked parent.
        if any(part.is_symlink() for part in [root, *root.absolute().parents]):
            parser.error(f"Repository path contains a symlink: {root}")
        resolved = root.resolve()
        if resolved in roots:
            continue
        roots.add(resolved)
        try:
            scan_root(inventory, root, args.max_depth, remaining, args.max_bytes)
        except ValueError as exc:
            parser.error(str(exc))
    if args.host_packages:
        host_packages(inventory)
    json.dump(inventory.finish(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

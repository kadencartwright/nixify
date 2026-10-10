#!/usr/bin/env python3
"""Evaluate/build a named local NixOS VM and run it in a separate directory."""

import argparse
import hashlib
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys


def invoke(command, **kwargs):
    print("+ " + shlex.join(map(str, command)), file=sys.stderr)
    return subprocess.run(command, check=True, **kwargs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["check", "dry-build", "build", "run"])
    parser.add_argument("--flake", type=Path, required=True, help="Local config directory")
    parser.add_argument("--host", default="demo", help="NixOS output name (default: demo)")
    parser.add_argument("--work-dir", type=Path, help="Separate build/disk directory")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", args.host):
        parser.error("--host must be a simple NixOS output name")
    flake = args.flake.expanduser().resolve()
    if not (flake / "flake.nix").is_file():
        parser.error("--flake must contain flake.nix")
    if args.mode == "run" and platform.system() != "Linux":
        parser.error("Run in a Linux VM/host. macOS needs a Linux builder and a separate guest runtime.")
    if not shutil.which("nix"):
        parser.error("Nix is required. See https://nix.dev/install-nix")

    # path: includes intended untracked config files, unlike Git flake filtering.
    target = f"path:{flake}#nixosConfigurations.{args.host}.config.system.build.vm"
    nix = ["nix", "--extra-experimental-features", "nix-command flakes"]
    # Never update a pin implicitly during testing.
    lock_options = ["--no-write-lock-file", "--no-update-lock-file"]
    if args.mode == "check":
        invoke(nix + ["eval", "--raw", target + ".drvPath"] + lock_options)
        return 0
    if args.mode == "dry-build":
        invoke(nix + ["build", "--dry-run", target] + lock_options)
        return 0

    digest = hashlib.sha256(str(flake).encode()).hexdigest()[:10]
    default_work = Path.home() / ".cache" / "nixify" / "vm" / f"{args.host}-{digest}"
    work = (args.work_dir or default_work).expanduser().resolve()
    if work == flake or work.is_relative_to(flake):
        parser.error("--work-dir must be outside the source flake")
    work.mkdir(parents=True, exist_ok=True)
    result = work / "result-vm"
    invoke(nix + ["build", target, "--out-link", str(result)] + lock_options)
    if args.mode == "build":
        print(f"VM runner: {result}/bin", file=sys.stderr)
        return 0

    runners = sorted((result / "bin").glob("run-*-vm"))
    if len(runners) != 1 or not runners[0].is_file():
        raise RuntimeError(f"Expected one VM runner in {result}/bin, found {len(runners)}")
    disk = work / "guest.qcow2"
    if disk.is_symlink():
        raise RuntimeError(f"Refusing a symlink at the guest disk path: {disk}")
    env = os.environ.copy()
    env["NIX_DISK_IMAGE"] = str(disk)
    print(f"Guest disk (preserved): {disk}", file=sys.stderr)
    print("Shut down with sudo poweroff; console exit: Ctrl+A, then X.", file=sys.stderr)
    invoke([str(runners[0])], cwd=work, env=env)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"nixify-vm: {exc}", file=sys.stderr)
        sys.exit(1)

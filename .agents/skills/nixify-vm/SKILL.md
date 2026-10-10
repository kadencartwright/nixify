---
name: nixify-vm
description: Build and run a disposable NixOS virtual machine to test a configuration before installation. Use for evaluation, VM-only overrides, boot checks, and use-case verification on Linux or a macOS migration path.
---

# Try the configuration in a VM

VM testing is optional. Test the user's configuration without activating it on the host. Explain which behaviors the VM can verify and which require actual hardware.

## Choose the path

Identify the host OS/architecture, Nix availability, target guest architecture, available RAM/disk space, and the config output. Read [references/platforms.md](references/platforms.md) for Linux and macOS prerequisites and the distinction between a direct-boot config VM and an installation test.

For a starter config, `demo` and `demo-arm` already import shared use cases and a VM-only module. For an existing physical host, use its `virtualisation.vmVariant` or a separate VM output sharing its modules. Override hardware storage, boot assumptions, unavailable devices, secret-dependent services, and login only inside the VM variant. Use the pinned Nixpkgs VM module. A physical output may have firmware/disk assertions which need a deliberate VM-only replacement.

Disposable login credentials belong only to VM modules. Prefer console login; if SSH is needed, bind forwarded ports to `127.0.0.1` and use a disposable key. Do not expose the guest's test password to the LAN, attach physical disks, or mount the user's home directory by default.

## Evaluate, build, run

The reusable helper works with local flakes and named outputs:

```bash
python3 scripts/vm.py --flake /path/to/my-nixos --host demo check
python3 scripts/vm.py --flake /path/to/my-nixos --host demo dry-build
python3 scripts/vm.py --flake /path/to/my-nixos --host demo build
python3 scripts/vm.py --flake /path/to/my-nixos --host demo run
```

Resolve the script relative to this skill folder. `check` evaluates the selected VM derivation; it does not build or boot it. `dry-build` reports build work. `build` creates the QEMU runner. `run` launches it on Linux. The helper sets a separate work directory and virtual disk and never calls `switch` or an installer. Generate and commit a lock before treating a test as reproducible.

Git flakes see tracked/staged files. Stage only the intended config files, or use `--include-untracked` for a reviewed, clean config directory. That flag uses `path:` and copies **all** directory contents to the Nix store, including ignored files. A non-Git directory also includes all files. Do not point it at a folder containing plaintext secrets or unrelated private data.

Use `--work-dir` to select space on a larger filesystem. A fresh work directory gives a clean guest; persistent virtual disks retain users/passwords and can hide a changed initial password. Do not delete a guest disk that contains user work without permission. The helper preserves disks and does not provide an automatic destructive reset.

## Verify the promised behavior

Boot the guest, log in, and exercise the use cases from the configuration report: required commands, service status, networking, project shell entry, and a desktop session if selected. Run small functional checks; installed package names alone are insufficient. Capture useful logs for failures. Do not label a guest tested if you only evaluated its derivation.

Write `vm-report.md` alongside the config with the pin/output, commands run, evaluation/build/boot/use-case results separately, disk/work directory, and remaining hardware checks. Stop the guest gracefully. Explain how to return to the same disk or start a fresh disposable instance. A direct-boot VM does not establish that real partitioning, encryption, EFI boot, Wi-Fi, fingerprint readers, or GPU drivers work.

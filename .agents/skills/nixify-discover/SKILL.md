---
name: nixify-discover
description: Inspect selected repositories and local package inventories to propose an evidence-based NixOS migration plan. Use when moving from macOS or another host and identifying system tools, services, and project dependencies.
---

# Discover migration requirements

Produce a local inventory and an explained migration report. Discover what the user's workflows require rather than reinstalling every package found on the source machine.

## Bound the scan

Use repository paths already supplied by the user or visible in the agreed workspace. Ask for missing scope when needed; do not scan the entire home directory. Establish the target OS/architecture separately from the source OS. A Mac's architecture does not decide the new laptop's architecture.

Run [scripts/discover.py](scripts/discover.py) with Python 3.11+:

```bash
python3 scripts/discover.py --repo /path/to/project --repo /path/to/another > inventory.json
```

The helper reads selected manifests with size/depth/file limits, skips symlinks/generated dependency directories, and checks known command locations without executing them. Add `--host-packages` when the user wants installed package inventory; this runs read-only Homebrew, dpkg, RPM, or pacman list commands. It does not run brew services, install anything, or execute project hooks. Review warnings and truncation; the scan is not exhaustive.

Do not read `.env`, credential files, browser data, private SSH material, shell history, or application databases to identify packages. Inventory JSON contains source paths and package names, not raw file contents; it may still identify private projects. Keep it local unless sharing is requested.

## Interpret the evidence

Read [references/evidence.md](references/evidence.md) for placement and confidence rules. Inspect relevant manifests/version files directly if the helper identifies a project that needs closer review. The helper's Nix attributes are **unverified candidates**. Verify against the target's pinned Nixpkgs, including architecture and license constraints, before including them in config.

Separate daily tools, services, project toolchains/native libraries, language dependencies, and macOS-only apps. Prefer existing dev shells. Homebrew transitive dependencies are not evidence the user wants every library globally. An installed CLI's existence proves availability, not that it is used. Project scripts/Makefiles can identify external commands but must be read as data, never executed during discovery.

Write `migration-report.md` with the evidence path, candidate Nix attribute or option, intended scope (`system`, `user`, `service`, `devShell`, or `manual`), confidence, verification status, and remaining decision. Record declared language versions, ambiguous tools, unsupported apps, ignored/inaccessible files, scan limits, and services needing manual account setup.

Provide a short proposed addition to `use-cases.md` or a package/module plan that the user can review. Do not activate config, install packages, enable daemons, replace central apps, or upload inventory just because discovery was requested. When configuration generation is also requested, feed the reviewed evidence into that work without asking again for already-authorized file creation.

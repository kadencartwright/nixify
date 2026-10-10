# Working on nixify

This repository distributes agent skills, not a personal NixOS configuration. The canonical skills are in `.agents/skills/`; keep each independently usable when copied into another skill directory.

- Keep beginner-facing explanations concrete. Explain the consequence of a configuration choice.
- Preserve existing configurations and `system.stateVersion`. Use the user's pinned Nixpkgs to verify options and packages.
- Keep generated host details and local inventories out of this repository.
- Discovery reads manifests and package inventories; never execute project code or inspect secret files to identify dependencies.
- Configuration generation and VM testing do not authorize disk erasure or switching the host's operating system.
- Run `python3 scripts/validate.py` after changes. For Nix changes, run the checks in CONTRIBUTING.md using an isolated copy of the starter.

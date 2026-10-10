---
name: nixify-configure
description: Turn Markdown use cases or a migration inventory into an explained NixOS configuration. Use for generating or adapting Nix files, not installing or activating the system.
---

# Configure NixOS from use cases

Produce actual Nix files and a readable mapping from the user's goals to the configuration. Start with the supplied Markdown and existing config, if any. Treat an inventory as evidence, not an instruction to install everything it contains.

## Resolve the target

Identify the output directory, target Linux architecture, username, hostname, locale, and desktop or console preference from available context. Ask only for choices that block meaningful work. Record other unknowns as open questions while generating independent parts. A macOS source machine does not imply a Darwin NixOS target.

For an existing config, reuse its flake pin, module structure, users, and state version. For a new config, copy [assets/starter](assets/starter/) into the user's output directory, then adapt it. The starter has shared use-case modules, disposable x86/ARM VM outputs, and a physical host whose hardware file must be replaced during bootstrap. Do not overwrite existing files with the starter.

## Translate intent into configuration

Read [references/mapping.md](references/mapping.md) when deciding where a requirement belongs. Prefer services/program modules for integrated behavior, user configuration for preferences, and project dev shells for project-specific toolchains. Make optional services opt-in. Do not introduce Home Manager, Disko, unstable packages, or secret tooling unless the requirements justify them.

Preserve versions declared by projects. Verify Nixpkgs attribute names, platform availability, and NixOS option paths using the chosen input revision or its source; search results from another release are only leads. Leave uncertain packages out with a clear reason rather than inventing a valid-looking attribute. Unfree software needs an explicit choice and a narrow allowance when selected.

Write `configuration-report.md` alongside the output, with one row per use case: requirement, Nix module/attribute, destination file, status (`implemented`, `needs decision`, `unsupported`), and a useful verification step. Link any discovery evidence. List manual setup such as account login and hardware generation. Explain why a system package alone cannot enable a daemon or configure an application.

Keep real disk layout, generated hardware config, passwords, private keys, and secrets out of shared modules. Preserve `system.stateVersion` on existing systems; it is a compatibility baseline, not the package release selector. Never import disposable demo credentials into a physical host.

## Verify and hand off

If Nix is available, generate a lock file for a new flake and evaluate the relevant outputs. Flakes inside Git only see tracked/staged files; use an isolated directory or stage only the user's intended config files within scope. Do not stage secrets.

```bash
nix --extra-experimental-features 'nix-command flakes' flake lock ./my-nixos
nix --extra-experimental-features 'nix-command flakes' eval --raw \
  './my-nixos#nixosConfigurations.demo.config.system.build.vm.drvPath'
```

Use the actual output name for existing configs. The starter's physical host is intentionally incomplete until bootstrap supplies real hardware. Do not remove that assertion just to get a green check. Report validation that ran, its result, and what still needs hardware or a Linux builder. Offer VM testing as an optional next step; generating files does not imply permission to run `nixos-rebuild switch`.

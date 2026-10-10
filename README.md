# nixify

Describe what you want your computer to do. Let a coding agent help turn that into a NixOS configuration you can understand, try in a VM, and install when you are ready.

Nixify is a collection of four agent skills, with a small NixOS starter and a few reusable helpers. You do not need to learn the Nix language before writing your requirements.

| Skill | What to ask your agent |
| --- | --- |
| [`nixify-configure`](.agents/skills/nixify-configure/SKILL.md) | “Turn my `use-cases.md` into a NixOS configuration.” |
| [`nixify-bootstrap`](.agents/skills/nixify-bootstrap/SKILL.md) | “Help me install my configuration from a NixOS USB installer.” |
| [`nixify-vm`](.agents/skills/nixify-vm/SKILL.md) | “Try my configuration in a disposable virtual machine.” |
| [`nixify-discover`](.agents/skills/nixify-discover/SKILL.md) | “Look at my Mac and coding projects and suggest what I need on Linux.” |

## Start here

```bash
git clone https://github.com/kadencartwright/nixify.git
cd nixify
cp examples/use-cases.md use-cases.md
```

Edit `use-cases.md` in plain English. Open this folder in a coding agent with skill support, then ask:

> Use $nixify-configure to turn use-cases.md into a NixOS configuration in ./my-nixos. Explain the choices and tell me what still needs an answer.

The skills live in `.agents/skills`, which supports repository-local discovery in Codex. For an agent that uses another skill directory, copy the four skill folders into its documented location, or explicitly ask it to read the linked `SKILL.md`. Keep each folder's scripts, references, and assets together. No connector or paid API is required by these skills.

A useful path through the skills is:

1. **Discover** the tools you use now, if you are migrating an existing machine.
2. **Configure** from your use cases and the discovery report.
3. **Try a VM**, optionally, before touching your disk.
4. **Bootstrap** from the official NixOS installer onto your chosen machine.

The agent produces actual Nix files and a requirements-to-configuration report. Ambiguous choices are recorded, and unsupported applications get an honest migration plan. A list of software alone is not enough to configure working services, users, networking, or hardware.

## Try the included starter

On a Linux machine with Nix and flakes enabled:

```bash
cp -R .agents/skills/nixify-configure/assets/starter ./my-nixos
python3 .agents/skills/nixify-vm/scripts/vm.py --flake ./my-nixos \
  --host demo --include-untracked run
```

The console demo has a disposable `demo` account with password `demo`. Shut it down with `sudo poweroff`; the QEMU console escape is `Ctrl+A`, then `X`. For ARM Linux, change `--host demo` to `--host demo-arm`. The helper puts builds and virtual disks in a separate work directory.

`--include-untracked` works with the freshly copied starter even inside another Git checkout. It copies all source files into the Nix store, so use a clean config folder without secrets. For an existing Git configuration, prefer tracked/staged files and the helper's default source handling.

`demo` and `demo-arm` share the starter's `modules/use-cases.nix` with the real `my-pc` host. The physical host deliberately cannot evaluate until its hardware file is generated during installation. It has no disk identifiers, passwords, SSH keys, or personal settings copied from another machine.

Nix is a package manager; NixOS is the Linux operating system. Running the Linux VM build on macOS needs a Linux builder or an existing Linux VM. The VM skill explains the macOS path; it does not treat Darwin as a Linux build target. Bare-metal Apple Silicon installation needs a separate hardware-specific plan.

## Discover tools without installing anything

Python 3.11 or newer is sufficient for discovery; Nix is not needed:

```bash
python3 .agents/skills/nixify-discover/scripts/discover.py \
  --repo /path/to/project --repo /path/to/another-project > inventory.json
```

Add `--host-packages` to query installed Homebrew, Debian, RPM, or Arch package names where available. The default checks known tool locations and reads selected project manifests; it does not run project code, traverse your whole home directory, or read credentials. Inventory is local and can include private project or package names. Review it before sharing. The agent turns evidence into a migration report and validates package names against the chosen Nixpkgs revision.

## Where this came from

Inspired by [kadencartwright/nix-install](https://github.com/kadencartwright/nix-install): shared modules, host-specific hardware, use-case/package mapping, guided ISO installation, and VM testing. Nixify starts smaller. Home Manager, Disko, encrypted storage, and secret management can be added when the requested setup needs them.

The starter uses a locked revision of the NixOS 26.05 branch. Keep `flake.lock` with your generated configuration. Skills check packages and options against that pin and preserve an existing `system.stateVersion`.

Authoritative references: [NixOS installation manual](https://nixos.org/manual/nixos/stable/#sec-installation-manual), [NixOS VM tutorial](https://nix.dev/tutorials/nixos/nixos-configuration-on-vm.html), and [Nix package search](https://search.nixos.org/packages).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for checks and realistic skill scenarios. Changes should help someone complete a task and understand the result. Keep personal hardware, credentials, and assumptions out of shared defaults.

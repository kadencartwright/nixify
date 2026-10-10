# Contributing

Python 3.11+ and PyYAML are needed for repository validation. The discovery helper itself uses only the Python standard library.

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py
```

Validation checks skill metadata and local references, parses Nix files when `nix-instantiate` is available, and runs behavioral tests for discovery and the VM helper.

For Nix evaluation, use a temporary copy so the starter asset is unchanged:

```bash
validation_dir=$(mktemp -d)
cp -R .agents/skills/nixify-configure/assets/starter/. "$validation_dir/"
cp flake.lock "$validation_dir/flake.lock"
nix --extra-experimental-features 'nix-command flakes' flake check --no-build
nix --extra-experimental-features 'nix-command flakes' eval --raw \
  "$validation_dir#nixosConfigurations.demo.config.system.build.vm.drvPath"
nix --extra-experimental-features 'nix-command flakes' eval --raw \
  "$validation_dir#nixosConfigurations.demo-arm.config.system.build.vm.drvPath"
```

The root flake contains test outputs. Do not run `flake check` against the unprepared starter: its physical `my-pc` output intentionally fails until hardware configuration is supplied. CI verifies that failure separately.

CI also boots a console guest with a NixOS test and verifies login and the tools promised by the demo. This tests the guest, not physical installation, firmware, graphics, Wi-Fi, or a real disk layout.

Exercise skills with realistic requests after instruction changes. Use a temporary output directory and do not activate configurations or erase disks during validation:

| Request | Observable outcome |
| --- | --- |
| Convert `examples/use-cases.md` | A config plus mapping; Node belongs in a dev shell, Docker stays disabled, encryption remains an open question. |
| Scan a macOS project with `Brewfile`, Node and Python manifests | Evidence is cited; language libraries are not all installed globally; macOS-only casks remain unresolved. |
| Install on a dual-boot laptop with no disk selected | The agent prepares a plan and asks for the missing target; it does not format a default disk. |
| Test the physical host in a VM | Hardware storage and secrets are isolated; test credentials stay inside the VM variant. |
| Run VM work from Apple Silicon macOS | The agent identifies the Linux-builder requirement instead of building `aarch64-darwin` as NixOS. |

Prefer narrow fixes backed by these outcomes. Do not add another mandatory tool, a large package catalog, or a universal desktop preference to solve one person's setup.

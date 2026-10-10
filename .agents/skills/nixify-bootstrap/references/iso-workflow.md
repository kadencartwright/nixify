# ISO configuration handoff

These commands start **after** the user-approved storage plan has been executed and the root and boot filesystems are mounted under `/mnt`. They do not partition or format a disk. Adapt directory, host, and user names to the reviewed configuration.

## Inspect and connect

The skill's preflight helper reports firmware mode, package/tool availability, memory, disks and mounts. It performs no writes. Disk identity and serials are useful locally; redact them before publishing logs.

Use `nmcli device status` to check connectivity. On a graphical ISO, `nmtui` or its network UI may be available. On a minimal ISO without NetworkManager, use the release manual's `wpa_supplicant`/`wpa_cli` Wi-Fi instructions. Confirm DNS and the Nix cache are reachable. Avoid putting a Wi-Fi passphrase in a command that will be recorded by the agent.

Check that `/mnt` is the target root, not the ISO's overlay. Use `findmnt /mnt` and `findmnt /mnt/boot`. For low-memory installs, evaluate RAM and available target space before choosing temporary swap; do not create an unencrypted swap file for an encrypted install.

## Keep the reviewed configuration on disk

Clone/copy the **user's generated configuration repository**, not the nixify skill repository, to `/mnt/etc/nixos`. Review its commit and `flake.lock`. For a local generated folder, copy its contents there. If that destination already exists, inspect and preserve it instead of replacing it blindly.

For a starter-derived `my-pc` configuration:

```bash
sudo nixos-generate-config --root /mnt --show-hardware-config \
  | sudo tee /mnt/etc/nixos/hosts/my-pc/hardware-configuration.nix >/dev/null
```

This replaces the starter's intentional assertion with detected filesystems and initrd modules. Inspect the result. When Disko owns filesystems, reconcile overlapping declarations instead of blindly importing a second conflicting layout. Hardware generation describes mounted storage; it does not choose or prepare the disk.

Set the host's bootloader and username to the values in the plan. `alex` in the starter is an example to replace. For a Git checkout, make the changed configuration files visible to Nix by staging those files, or evaluate an explicit `path:` reference; do not stage secrets. Generate/retain `flake.lock` with flakes enabled if it is not already present.

## Evaluate, install, set credentials

```bash
sudo nix --extra-experimental-features 'nix-command flakes' eval --raw \
  'path:/mnt/etc/nixos#nixosConfigurations.my-pc.config.system.build.toplevel.drvPath'
sudo nixos-install --flake 'path:/mnt/etc/nixos#my-pc'
sudo nixos-enter --root /mnt -c 'passwd alex'
```

Run password entry in the user's interactive terminal. `nixos-install` normally prompts for a root password; do not bypass credential setup by using the VM's password or copying a plaintext password into a Nix file. If the process fails, diagnose the named stage and retry that stage. Do not erase storage again.

Before reboot, verify the user exists in the installed passwd database, their password is set, `/boot` contains the expected loader/EFI files, and the config/lock are present under the target root. Root access alone is not a successful desktop login. Do not require the user to reveal password hashes.

After first boot:

```bash
nmcli device status
cd /etc/nixos
sudo nixos-rebuild build --flake .#my-pc
```

A later `sudo nixos-rebuild switch --flake .#my-pc` activates a reviewed update when requested. To recover, select an older generation from the boot menu. A broken boot can be repaired from the ISO by mounting the same layout, fixing config, and reinstalling without reformatting.

Sources: [installation manual](https://nixos.org/manual/nixos/stable/#sec-installation-manual), [Disko](https://github.com/nix-community/disko), [flake source handling](https://nix.dev/manual/nix/stable/command-ref/new-cli/nix3-flake.html).

# VM platform choices

## Linux

Nix can evaluate a Linux guest on a non-NixOS Linux host. Local builds need a builder for the guest architecture. x86_64 Linux usually uses `demo`; aarch64 Linux uses `demo-arm`. A differently sized guest instruction set requires an explicitly configured builder/emulation; do not silently enable system-wide emulation.

Check access to `/dev/kvm` for acceleration. If KVM is unavailable, QEMU software emulation may work more slowly. Check available disk space for the Nix store and VM image; memory size is not a disk budget. The starter uses a 2 GiB console guest with an 8 GiB virtual disk. Desktop guests usually need more RAM and a working display backend.

For physical outputs, a typical VM-only adjustment is:

```nix
virtualisation.vmVariant = {
  virtualisation.memorySize = 4096;
  virtualisation.cores = 2;
  users.users.vmtest = {
    isNormalUser = true;
    initialPassword = "test-in-disposable-vm-only";
    extraGroups = [ "wheel" ];
  };
};
```

This is an example to adapt. A real config may also need VM-only overrides for storage, existing password policies, hardware assertions, or sops/TPM services. NixOS evaluates the VM variant with `qemu-vm.nix`; do not add `virtualisation.memorySize` at the top level of an ordinary physical config where that option is not defined.

The helper's default work directory includes a hash of the source path and output name. `NIX_DISK_IMAGE` points at its private guest image. Guest shutdown is `sudo poweroff`; with a console QEMU runner, `Ctrl+A`, then `X` exits QEMU.

## macOS

macOS can use Nix packages, but NixOS guests use `x86_64-linux` or `aarch64-linux`, never `*-darwin`. Nix does not automatically build Linux derivations on a Darwin builder.

For beginners, use an existing Linux VM or an official NixOS ISO in a VM app and perform the build/test inside it. Use an aarch64 Linux guest on Apple Silicon, and an x86_64 Linux guest on Intel. A nested QEMU guest may have no acceleration; testing the config through the outer guest can be more practical.

For a configured remote Linux builder, evaluation/build from macOS is possible. Running the generated runner directly on macOS additionally requires Darwin host packages/QEMU via `virtualisation.host.pkgs` and an appropriate backend. The helper intentionally refuses `run` on macOS and points to the Linux path; do not imply it manages a macOS VM app.

Offer the native VM app/ISO route or a Linux builder based on the user's existing tools. Installing a builder or VM app is a separate prerequisite to explain, not a hidden mutation.

## Configuration VM versus installer test

`config.system.build.vm` boots with a synthetic disk layout. It checks users, packages, services, and application behavior. `vmWithBootLoader` checks more of guest bootloader behavior, still with synthetic storage.

To test the real installation workflow, boot the chosen official ISO in a disposable VM, attach a new virtual disk, and follow the reviewed install plan against that virtual disk. Existing Disko/nixos-anywhere installation tests can be used when the project already supports them. Do not reuse physical disk paths or claim a direct-boot result proves installation success.

Sources: [NixOS VM tutorial](https://nix.dev/tutorials/nixos/nixos-configuration-on-vm.html), [build-vm implementation](https://github.com/NixOS/nixpkgs/blob/nixos-26.05/nixos/modules/virtualisation/build-vm.nix), [distributed builds](https://nix.dev/manual/nix/stable/advanced-topics/distributed-builds.html), [Darwin VM host configuration](https://wiki.nixos.org/wiki/NixOS_virtual_machines_on_macOS).

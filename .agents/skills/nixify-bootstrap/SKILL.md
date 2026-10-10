---
name: nixify-bootstrap
description: Guide a NixOS installation from an official ISO using a prepared configuration. Use for live-USB preparation, target inspection, storage planning, hardware generation, installation, and first boot.
---

# Bootstrap from the NixOS ISO

Help the user reach a working first boot with their chosen configuration. Read the config and its report first; configuration generation and VM testing are not authorization to erase a disk.

## Prepare the installation

Determine whether this is a fresh install, an existing NixOS system, dual boot, or a disposable VM. Establish the target machine, Linux architecture, firmware mode, chosen configuration output, account name, storage/encryption preference, and backup status. A macOS source machine can be used to prepare media; do not assume its internal disk is the installation target. Bare-metal Apple Silicon and Raspberry Pi boot layouts need hardware-specific instructions, not the x86 UEFI recipe.

Use the [official download page](https://nixos.org/download/) and the manual for the selected release. Verify the image against its published checksum. Identify the USB device before writing it; writing an ISO erases that device too. The graphical installer is a useful beginner option; a prepared flake can be installed through the live environment's terminal.

In the booted ISO, use [scripts/preflight.sh](scripts/preflight.sh) for read-only inspection, or equivalent commands. Confirm network access, firmware mode, RAM/store capacity, disk identity and mounted filesystems. Read [references/iso-workflow.md](references/iso-workflow.md) for the config handoff and first boot.

## Make the destructive step concrete

Prepare an `install-plan.md` identifying the exact disk by stable `/dev/disk/by-id` path where available, model, serial, capacity, partitions to preserve or erase, filesystem/encryption layout, mounts, host output, and the specific commands to run. Preserve a dual-boot EFI partition and existing data unless the user chose otherwise. Never pick the first disk, reuse another host's UUIDs, or run a whole-disk wipe for a partition-preserving install.

Use existing authorization if it explicitly covers this exact target and operation. Otherwise show the completed plan and obtain permission before writing the USB, partitioning, formatting, or running Disko's destructive modes. Inspect again immediately before execution; stop if disk identity, mounts, or the requested layout differ. Retrying a failed install does not justify repartitioning a successfully prepared disk.

Disko is optional. If selected, use a pinned input and the project's layout, inspect the generated operation and secret handling, and run it against the confirmed disk only. For manual storage, use the selected release's official recipe adapted to the concrete plan. Collect encryption passphrases interactively outside transcripts and Git; retain a recovery method when TPM unlock is requested.

## Install and verify first boot

Once the planned filesystems are mounted under `/mnt`, generate target hardware configuration and place it in the chosen host directory. Adapt bootloader configuration to the actual firmware, including `/boot` mount and EFI access. Keep the flake and its lock inside the installed system so rebuilds are possible after removing the USB.

Evaluate the physical output, install it, set the declared user's password interactively, and verify the installed account and boot files before rebooting. Report the config path, first login, network connection, and rebuild command. Keep the installer attached until reboot has begun. After first boot, verify login, networking, and the user-requested services; explain rollback from the boot menu and retain the USB for recovery.

Do not silently run a post-install `switch` from a floating remote branch. Use the reviewed local configuration and lock. If you cannot access the ISO or machine, finish the concrete config and plan and state which commands the user must run; do not claim an installation happened.

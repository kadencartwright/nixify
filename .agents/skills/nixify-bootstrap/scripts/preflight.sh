#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == --help ]]; then
  printf '%s\n' 'Usage: preflight.sh' 'Read-only Linux ISO inspection. No sudo, disk writes, or credential reads.'
  exit 0
fi
if (($#)); then
  printf 'Unexpected argument: %s\n' "$1" >&2
  exit 2
fi
if [[ "$(uname -s)" != Linux ]]; then
  printf '%s\n' 'Run this helper in the booted Linux installer, not on the source Mac.' >&2
  exit 1
fi

printf 'Machine: %s\n' "$(uname -m)"
if [[ -d /sys/firmware/efi ]]; then
  printf '%s\n' 'Firmware boot: UEFI'
else
  printf '%s\n' 'Firmware boot: BIOS (or EFI interface unavailable)'
fi
for tool in nix nixos-install nixos-generate-config lsblk findmnt nmcli wpa_cli; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf 'Available: %s\n' "$tool"
  else
    printf 'Missing: %s\n' "$tool"
  fi
done
if command -v free >/dev/null 2>&1; then free -h; fi
if command -v lsblk >/dev/null 2>&1; then
  lsblk --json -o NAME,PATH,TYPE,SIZE,MODEL,SERIAL,FSTYPE,MOUNTPOINTS,TRAN
fi
if command -v findmnt >/dev/null 2>&1; then
  findmnt --target /mnt
fi
printf '%s\n' 'No disk has been selected or modified.'

# Requirement mapping

| User intent | Configuration destination | What to check |
| --- | --- | --- |
| Use a terminal tool everywhere | `environment.systemPackages`, or a user's packages | Is it available for the target platform in the pinned Nixpkgs? |
| Work on a versioned language project | Project `devShells`, preserving an existing shell | Runtime versions and native build dependencies, not every language library globally. |
| Run Docker containers | `virtualisation.docker.enable` when Docker is chosen | Explain daemon access and membership in the `docker` group; do not replace Docker with Podman silently. |
| Use Wi-Fi | `networking.networkmanager.enable` | Firmware and device support still need hardware verification. Do not copy Wi-Fi secrets into Nix. |
| Have working audio | PipeWire NixOS module and session integration | Enabling an audio package alone is insufficient. |
| Print documents | `services.printing` and applicable drivers/discovery | Hardware-dependent drivers; avoid opening remote admin access by default. |
| Receive SSH connections | `services.openssh`, public keys, firewall policy | A requested local SSH client does not imply an SSH server. |
| Choose an editor or shell | Appropriate `programs` module; user preferences if needed | NixOS and Home Manager have different option namespaces. |
| Use a macOS app | Linux equivalent, web app, or retain a macOS workflow | A Homebrew cask name is not automatically a Linux package. Ask before replacing a central workflow. |
| Store a token or password | Runtime secret file or selected secret manager | Nix files and the Nix store are not secret storage, even in a private Git repo. |

Use this as a placement guide, not a verified package catalog. Options change across releases. Check the pin before writing code.

For a simple Node project, a generated `flake.nix` dev shell can use `pkgs.mkShell { packages = [ pkgs.nodejs ]; }`. Select a versioned attribute only after checking the project's `engines`, version files, and pinned package availability. Keep npm libraries in the project's package manager. Use `pkgs.stdenv.cc` when native extension compilation actually requires a compiler.

The starter's `modules/use-cases.nix` is the initial shared destination. Split it into named modules as the requirements grow. The starter's `demo` and physical `my-pc` consume the same shared files; hardware-specific files are separate.

Sources: [package search](https://search.nixos.org/packages), [option search](https://search.nixos.org/options), [dev shells](https://nix.dev/tutorials/first-steps/declarative-shell.html), [state version](https://nixos.org/manual/nixos/stable/#sec-upgrading).

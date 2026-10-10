# Interpreting discovery evidence

The scanner makes suggestions, not a lock file or a package conversion. All generated Nix attributes have `verified: false`. Resolve them against the chosen Nixpkgs input before writing config.

| Evidence | Strength | How to interpret it |
| --- | --- | --- |
| Existing Nix dev shell | Strong intent | Preserve it; its commands and native libraries already have a home. |
| Manifest + declared runtime version | Strong project requirement | Put the matching toolchain in a project environment. Version availability still needs verification. |
| Build file using `pkg-config` or a native library | Strong only for that project | Add build/native dependencies to its dev shell, not automatically to global packages. |
| Dockerfile or Compose file | Container workflow | Determine whether the user needs a local daemon, remote Docker CLI, or another runtime. |
| Explicit Brewfile formula/cask | User-maintained choice | Formula names and casks still need Linux equivalents; a tap is not a package. |
| Package manager inventory | Installed, perhaps transitive | Treat as a lead; do not copy the whole list into system packages. |
| Tool found on PATH | Available | Lower confidence; may be stale or unused. |
| A macOS-only cask | Platform boundary | Record a web app, Linux equivalent, retained Mac workflow, or unresolved decision. |

Important distinctions:

- `package.json` dependencies belong to npm/pnpm/yarn, not `environment.systemPackages`. A native module may need system libraries, but inspect its installation requirements rather than guessing from its name.
- Python libraries stay in the project's environment. Native extension builds may need `stdenv.cc`, `pkg-config`, or named libraries; only add what evidence supports.
- Existing `flake.nix`, `shell.nix`, or `devenv.nix` is inventoried, never evaluated by discovery. Evaluating it later is a separate configuration task.
- A Homebrew `postgresql@...` formula suggests a version requirement. It does not decide whether the user wants a NixOS PostgreSQL service, a client, or a development container.
- macOS `launchd` services do not translate into a working systemd service by copying package names.
- NixOS does not provide the conventional filesystem layout expected by arbitrary downloaded binaries. Prefer packaged tools, dev shells, or an explicit container plan for unsupported tooling.

The helper intentionally does not extract arbitrary shell recipes or maintain a universal brew-to-Nix database. Unknown packages remain in `unmapped_packages`, with the evidence necessary for an agent to research them. A guessed attribute is worse than an unresolved item.

Sources: [Nixpkgs package search](https://search.nixos.org/packages), [declarative development shells](https://nix.dev/tutorials/first-steps/declarative-shell.html), [Nixpkgs manual](https://nixos.org/manual/nixpkgs/stable/).

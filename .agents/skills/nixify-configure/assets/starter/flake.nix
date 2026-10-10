{
  description = "A small, explained NixOS configuration";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { nixpkgs, ... }:
    let
      mkSystem = system: extraModules: nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [ ./modules/common.nix ./modules/use-cases.nix ] ++ extraModules;
      };
    in {
      nixosConfigurations = {
        demo = mkSystem "x86_64-linux" [ ./modules/vm.nix ];
        demo-arm = mkSystem "aarch64-linux" [ ./modules/vm.nix ];
        my-pc = mkSystem "x86_64-linux" [ ./hosts/my-pc/default.nix ];
      };
    };
}

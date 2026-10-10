{
  description = "Nixify skill assets and a NixOS VM smoke test";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { nixpkgs, ... }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forSystems = nixpkgs.lib.genAttrs systems;
      starter = ./.agents/skills/nixify-configure/assets/starter;
    in {
      templates.default = {
        path = starter;
        description = "Small NixOS config with shared use cases and disposable VMs";
      };
      checks = forSystems (system:
        let pkgs = import nixpkgs { inherit system; };
        in {
          vm-boot = pkgs.testers.runNixOSTest {
            name = "nixify-console-demo";
            nodes.machine = { lib, ... }: {
              imports = [
                (starter + "/modules/common.nix")
                (starter + "/modules/use-cases.nix")
                (starter + "/modules/vm.nix")
              ];
              virtualisation.memorySize = lib.mkForce 768;
            };
            testScript = ''
              machine.start()
              machine.wait_for_unit("multi-user.target")
              machine.wait_for_unit("NetworkManager.service")
              machine.succeed("id demo")
              machine.succeed("su - demo -c 'git --version && rg --version && fd --version'")
              machine.succeed("su - demo -c 'sudo -n true'")
              machine.fail("systemctl is-active sshd.service")
            '';
          };
        });
    };
}

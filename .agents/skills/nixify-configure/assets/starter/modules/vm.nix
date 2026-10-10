{ modulesPath, ... }:
{
  # This module is imported only by disposable demo outputs.
  imports = [ (modulesPath + "/virtualisation/qemu-vm.nix") ];
  networking.hostName = "nixify-demo";

  virtualisation = {
    memorySize = 2048;
    cores = 2;
    diskSize = 8192;
    graphics = false;
  };

  users.users.demo = {
    isNormalUser = true;
    extraGroups = [ "wheel" ];
    initialPassword = "demo";
  };
  # Disposable console only: no SSH server or host port forwarding.
  security.sudo.wheelNeedsPassword = false;
}

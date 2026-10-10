{ ... }:
{
  imports = [ ./hardware-configuration.nix ];
  networking.hostName = "my-pc";

  # The bootstrap skill adapts this to the actual firmware/boot layout.
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  users.users.alex = {
    isNormalUser = true;
    extraGroups = [ "wheel" "networkmanager" ];
    # Set a real password interactively with nixos-enter before first boot.
  };
}

{ pkgs, ... }:
{
  # This is the initial installation baseline. Keep it on later upgrades.
  system.stateVersion = "26.05";

  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  networking.networkmanager.enable = true;
  networking.firewall.enable = true;

  time.timeZone = "UTC";
  i18n.defaultLocale = "en_US.UTF-8";
  console.keyMap = "us";

  environment.systemPackages = [ pkgs.git pkgs.vim ];
}

{ ... }:
{
  assertions = [{
    assertion = false;
    message = "Generate hardware-configuration.nix on the mounted target with nixos-generate-config --root /mnt. Replace this file before installing my-pc.";
  }];
}

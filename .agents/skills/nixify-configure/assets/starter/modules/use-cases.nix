{ pkgs, ... }:
{
  # Replace/extend these with packages and modules justified by use-cases.md.
  # Project language runtimes usually belong in the project's dev shell.
  environment.systemPackages = [ pkgs.ripgrep pkgs.fd ];
}

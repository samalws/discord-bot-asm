{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/75ad56bdc927f3a9f9e05e3c3614c4c1fcd99fcb.tar.gz") {} }:
pkgs.mkShell {
  buildInputs = [ (pkgs.python3.withPackages (p: [p.discordpy p.requests]))];
}

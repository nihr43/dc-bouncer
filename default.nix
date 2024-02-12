{ nixpkgs ? import <nixpkgs> {  } }:

let
  pkgs =  with nixpkgs.python311Packages; [
    ansible-runner
    kubernetes
    pyyaml
    types-pyyaml
  ];

in
  nixpkgs.stdenv.mkDerivation {
    name = "env";
    buildInputs = pkgs;
  }

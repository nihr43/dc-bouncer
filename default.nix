{ nixpkgs ? import <nixpkgs> {  } }:

let
  pkgs =  with nixpkgs.python311Packages; [
    ansible-runner
    kubernetes
  ];

in
  nixpkgs.stdenv.mkDerivation {
    name = "env";
    buildInputs = pkgs;
  }

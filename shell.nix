# shell.nix
{ pkgs ? import <nixpkgs> {} }:
let
  my-python-packages = p: with p; [
    pip
    # other python packages
  ];
  my-python = pkgs.python310.withPackages my-python-packages;
in my-python.env

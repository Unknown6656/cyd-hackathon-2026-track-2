{
  description = "Development environment for Track 2 Advisor";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python312
            uv
            git
            curl
          ];

          shellHook = ''
            echo "Track 2 Advisor Dev Shell"
            echo "Run with: uv run --project app scripts/test_api.py"
          '';
        };
      });
}

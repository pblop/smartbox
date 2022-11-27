{
  description = "Smartbox python package";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    nur.url = "github:nix-community/NUR";
  };

  outputs = { self, nixpkgs, nur }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      overlays = [
        (self: super: {
          nur = import nur {
            nurpkgs = self;
            pkgs = self;
          };
        })
      ];
    };
  in {
    devShells.${system}.default = let
      python = pkgs.nur.repos.graham33.home-assistant.python;
      smartbox = python.pkgs.smartbox.overridePythonAttrs (o: {
        propagatedBuildInputs = (o.propagatedBuildInputs or []) ++ (with python.pkgs; [
          # TODO: move to NUR
          pytest-benchmark
        ]);
      });
    in pkgs.mkShell {
      inputsFrom = [
        smartbox
      ];
      packages = with pkgs; [
        black
        mypy
      ];
      # Work around version check warning
      # https://github.com/pypa/pip/issues/11309
      shellHook = ''
        export PIP_DISABLE_PIP_VERSION_CHECK=true
      '';
    };
  };
}

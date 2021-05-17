with import <nixpkgs> {};
let
  python = python38.override {
    packageOverrides = pySelf: pySuper: {
      inherit (nur.repos.graham33.python3Packages) monkeytype;
      python-engineio = self.nur.repos.graham33.python3Packages.python-engineio_3;
      python-socketio = self.nur.repos.graham33.python3Packages.python-socketio_4;
      smartbox = nur.repos.graham33.python3Packages.smartbox.overrideAttrs (o: {
        src = ./.;
      });
    };
  };
  pythonEnv = python.withPackages (ps: with ps; [
    flake8
    smartbox
    monkeytype
    mypy
    # TODO: duplicating checkInputs from smartbox
    freezegun
    pytest
    pytest-asyncio
    pytest-mock
    pytest-randomly
    pytest-sugar
    requests-mock
    tox
  ]);
in mkShell {
  buildInputs = [
    black
    pythonEnv
  ];
}

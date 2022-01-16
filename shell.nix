with import <nixpkgs> {
  overlays = [
    (self: super: rec {
      home-assistant = super.nur.repos.graham33.home-assistant.override {
        packageOverrides = self.lib.composeExtensions super.nur.repos.graham33.homeAssistantPackageOverrides pythonOverrides;
      };

      pythonOverrides = (pySelf: pySuper: rec {
        smartbox = pySuper.smartbox.overridePythonAttrs (o: {
          src = ./.;
        });
      });
    })
  ];
};
let
  pythonEnv = home-assistant.python.withPackages (ps: with ps; [
    build
    flake8
    smartbox
    monkeytype
    mypy
    pip
    # TODO: duplicating checkInputs from smartbox
    freezegun
    pytest
    pytest-asyncio
    pytest-mock
    pytest-randomly
    pytest-sugar
    requests-mock
    tox
    twine
    types-requests
  ]);
in mkShell {
  buildInputs = [
    black
    pythonEnv
  ];
}

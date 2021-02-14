with import <nixpkgs> {
  overlays = [
    ( self: super: rec {
      python38 = super.python38.override {
        packageOverrides = pySelf: pySuper: {
          # make sure we use python-socketio 4.x, even in nixpkgs unstable
          python-engineio = self.nur.repos.graham33.python-engineio-3;
          python-socketio = self.nur.repos.graham33.python-socketio-4;
        };
      };
      python38Packages = python38.pkgs;
    })
  ];
};
with python38Packages;

buildPythonPackage rec {
  name = "smartbox";
  src = ".";

  nativeBuildInputs = [
    pytest
    flake8
    yapf
  ];

  propagatedBuildInputs = [
    aiohttp
    click
    python-socketio
    requests
    websocket_client
  ];

  checkInputs = [
    freezegun
    pytest-asyncio
    pytest-mock
    pytest-randomly
    requests-mock
    tox
  ];
}

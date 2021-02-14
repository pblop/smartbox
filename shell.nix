with import <nixpkgs> {};
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

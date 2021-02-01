with import <nixpkgs> {};
with python38Packages;

buildPythonPackage rec {
  name = "smartbox";
  src = ".";
  propagatedBuildInputs = [ aiohttp
                            click
                            flake8
                            python-socketio
                            requests
                            websocket_client
                            yapf
                          ];

  checkInputs = [ freezegun
                  pytest
                  pytest-asyncio
                  pytest-mock
                  pytest-randomly
                  requests-mock
                  tox ];
}

with import <nixpkgs> {};
with python38Packages;

buildPythonPackage rec {
  name = "smartbox";
  src = ".";
  propagatedBuildInputs = [ aiohttp
                            click
                            flake8
                            freezegun
                            pytest
                            pytest-asyncio
                            pytest-mock
                            pytest-randomly
                            python-socketio
                            requests
                            requests-mock
                            websocket_client
                            yapf
                          ];
}

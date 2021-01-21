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
                            python-socketio
                            pyyaml
                            requests
                            requests-mock
                            websocket_client
                            yapf
                          ];
}

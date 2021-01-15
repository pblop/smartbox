with import <nixpkgs> {};
with python38Packages;

buildPythonPackage rec {
  name = "smartbox";
  src = ".";
  propagatedBuildInputs = [ click
                            flake8
                            freezegun
                            pytest
                            pyyaml
                            requests
                            requests-mock
                            yapf
                          ];
}

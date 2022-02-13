with import <nixpkgs> {
  overlays = [
    (self: super: rec {
      home-assistant = super.nur.repos.graham33.home-assistant;
    })
  ];
};
let
  pythonEnv = home-assistant.python.withPackages (ps: with ps; [
    build
    flake8
    monkeytype
    mypy
    pip
    # TODO: duplicating buildInputs checkInputs from smartbox
    aiohttp
    click
    python-socketio_4
    pyyaml
    requests
    websocket_client
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

# Changelog

## 0.0.5 (alpha)

### Features
* Rename `away_status` to `device_away_status`
* Update API docs
* Add tox, tox and flake8 on github action

### Bug Fixes
* Pin dependency of python-socketio to match server

## 0.0.4 (alpha)

### Features
* Refactor socket session and implement reconnect
* Add note on basic auth credentials

## 0.0.3 (alpha)

### Features
* Fixed packaging

### Bug Fixes
* Fixed disconnect handling on token refresh

## 0.0.2 (alpha)

### Features
* Added `get_api_name` function
* Added basic tests for REST interactions
* Added token refresh support
* Added socket.io interface via `open_socket` function (no tests as yet)
* Added documentation for known REST and websocket endpoints

## 0.0.1 (alpha)

### Features
* Initial version supporting some REST endpoints

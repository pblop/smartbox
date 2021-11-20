# Changelog

## 0.3.0 (alpha)

### Features
* Try to reconnect the socketio connection multiple (3) times before giving up.
  This means we will take longer to refresh our token, but should deal better
  with transient connection issues.
* Implement retry for session HTTP requests. This should help avoid transient
  failures.

## 0.2.1 (alpha)

### Bug Fixes
* Handle HTTP errors from auth POST requests

## 0.2.0 (alpha)

### Features
* Added `mypy` type annotations
* Reformatted with `black`
* Added some more API notes

## 0.1.0 (alpha)
(same as 0.0.6, bumped minor version due to breaking change)

## 0.0.6 (alpha)

### Features
* Throw exception on auth failures

### Breaking Changes
* Allow APIs which don't start with 'api-' (@patrickbusch) - #6
  * Some installations use API names that don't start with 'api-'
  * You now must pass 'api-foo' where you previously passed 'foo' as the API
    name parameter

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

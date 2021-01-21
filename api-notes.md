# API notes
Some brief notes on the REST endpoints used by this library.

# REST API

## Auth

### /api/v2/client/token
POST: needs basic auth token provided in the `Authorization` header. See code
for access token and refresh protocol.

The endpoints below need the access token obtained from the token endpoint (see
code), which lasts for four hours before needing to be refreshed.

## Devices

### /api/v2/devs
GET: list devices

### /api/v2/grouped_devs
GET: list devices with extra grouping info

POST: TODO untested

### /api/v2/devs/<dev_id>/dev_data
GET: Appears to be all device data, including most of the information obtainable
via specific endpoints below.

POST: TODO untested

### /api/v2/devs/<dev_id>/geo_data
GET: device geolocation data

POST: TODO untested

### /api/v2/devs/<dev_id>/connected
GET: device connection status

POST: TODO untested

### /api/v2/devs/<dev_id>/mgr/away_status
GET: device away status

POST: TODO untested

### /api/v2/devs/<dev_id>/mgr/discovery
GET: device discovery status

POST: TODO untested

### /api/v2/devs/<dev_id>/htr_system/power_limit
GET: heater power limit info

POST: TODO untested

### /api/v2/devs/<dev_id>/mgr/rtc/time
GET: device date and time info

POST: TODO untested

## Nodes
Note: node type apparently can be `htr`, `thm` or `acm` (only htr tested).

### /api/v2/devs/<dev_id>/mgr/nodes
GET: lists nodes

### /api/v2/devs/<dev_id>/<node_type>/<node_addr>
GET: Appears to be all node data, including most of the information obtainable
via specific endpoints below.

POST: TODO untested

### /api/v2/devs/<dev_id>/<node_type>/<node_addr>/status
GET: get node status

POST: update node status. Only fields that are changing need to be supplied,
but `units` must be provided with any temperature fields.

### /api/v2/devs/<dev_id>/<node_type>/<node_addr>/select
GET: TODO: untested

POST: select node TODO: what does this mean?

### /api/v2/devs/<dev_id>/<node_type>/<node_addr>/prog
GET: get node programme

POST: TODO untested

### /api/v2/devs/<dev_id>/<node_type>/<node_addr>/type
GET: get node type

POST: TODO untested

### /api/v2/devs/<dev_id>/<node_type>/<node_addr>/version
GET: get node version info (firmware version etc)

POST: TODO untested

### /api/v2/devs/<dev_id>/<node_type>/<node_addr>/setup
GET: get node setup

POST: update node setup. Apparently all fields need to be provided even if
unchanged.

### /api/v2/devs/<dev_id>/<node_type>/<node_addr>/away_status
GET: get node away status

POST: update node away status. Only fields that are changing need to be
supplied.

### /api/v2/devs/<dev_id>/<node_type>/<node_addr>/samples
GET: TODO: untested

POST: TODO: untested

## Groups
TODO /api/v2/groups

## Users
TODO /api/v2/users

## Misc

### /version

Get version info

# Websocket API
This uses the [socket.io] protocol.

Briefly:
* The socket session is per device
* The access token and device ID must be supplied as query params
* On successful connection, the client should emit a `dev_data` event. The
  corresponding response from the server is similar to the dev_data REST
  endpoint above
* The server will send periodic `update` events containing node status updates
  similar to the node status API endpoints above, one per node.
* The client should send a `ping` message every 20s (in addition to the protocol
  level ping/pong). Have not tested that this is strictly necessary.

[socket.io]: https://socket.io/

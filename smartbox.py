import asyncio
import click
import datetime
import json
import logging
import pprint
import requests
import socketio
import urllib

_MIN_TOKEN_LIFETIME = 60  # Minimum time left before expiry before we refresh (seconds)


class Session(object):
    def __init__(self, api_name, basic_auth_credentials, username, password, verbose=False):
        self._api_name = api_name
        self._api_host = f"https://api-{self._api_name}.helki.com"
        self._basic_auth_credentials = basic_auth_credentials
        self._auth({'grant_type': 'password', 'username': username, 'password': password})
        self._verbose = verbose

    def _auth(self, credentials):
        token_data = '&'.join(f"{k}={v}" for k, v in credentials.items())
        token_headers = {
            'authorization': f'Basic {self._basic_auth_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        token_url = f"{self._api_host}/client/token"
        response = requests.post(token_url, data=token_data, headers=token_headers)
        r = response.json()
        self._access_token = r['access_token']
        self._refresh_token = r['refresh_token']
        if r['expires_in'] < _MIN_TOKEN_LIFETIME:
            logging.warning(
                f"Token expires in {r['expires_in']}s, which is below minimum lifetime of {_MIN_TOKEN_LIFETIME}s - will refresh again on next operation"
            )
        self._expires_at = datetime.datetime.now() + datetime.timedelta(seconds=r['expires_in'])
        logging.debug(
            f"Authenticated session ({credentials['grant_type']}), access_token={self._access_token}, expires at {self._expires_at}"
        )

    def _has_token_expired(self):
        return (self._expires_at - datetime.datetime.now()) < datetime.timedelta(seconds=_MIN_TOKEN_LIFETIME)

    def _check_refresh(self):
        if self._has_token_expired():
            self._auth({'grant_type': 'refresh_token', 'refresh_token': self._refresh_token})

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            # TODO: generalise
            "x-serialid": "5",
        }

    def _api_request(self, path):
        self._check_refresh()
        api_url = f"{self._api_host}/api/v2/{path}"
        response = requests.get(api_url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def _api_post(self, data, path):
        self._check_refresh()
        api_url = f"{self._api_host}/api/v2/{path}"
        # TODO: json dump
        try:
            data_str = json.dumps(data)
            logging.debug(f"Posting {data_str} to {api_url}")
            response = requests.post(api_url, data=data_str, headers=self._get_headers())
            response.raise_for_status()
        except requests.HTTPError as e:
            # TODO: logging
            logging.error(e)
            logging.error(e.response.json())
            raise
        return response.json()

    async def open_socket(self, device_id, dev_data_callback=None, node_update_callback=None):
        if self._verbose:
            sio = socketio.AsyncClient(logger=True, engineio_logger=True)
        else:
            logging.getLogger('socketio').setLevel(logging.ERROR)
            logging.getLogger('engineio').setLevel(logging.ERROR)
            sio = socketio.AsyncClient()

        class TokenExpiredExcepton(Exception):
            pass

        namespace = '/api/v2/socket_io'

        class SmartboxAPIV2Namespace(socketio.AsyncClientNamespace):
            def __init__(self, session, namespace=None):
                super().__init__(namespace)
                self._session = session
                self._connected = False
                self._received_message = False
                self._received_dev_data = False

            def on_connect(self):
                logging.debug(f"Namespace {namespace} connected")
                self._connected = True

            def on_disconnect(self):
                logging.info(f"Namespace {namespace} disconnected")
                self._connected = False
                self._received_message = False
                self._received_dev_data = False

                # check if we need to refresh our token
                if self._session._has_token_expired():
                    logging.info("Token expired, disconnecting")
                    sio.disconnect()

            async def on_dev_data(self, data):
                logging.debug(f"Received dev_data: {data}")
                self._received_message = True
                self._received_dev_data = True
                if dev_data_callback is not None:
                    dev_data_callback(data)

            async def on_update(self, data):
                logging.debug(f"Received update: {data}")
                if not self._received_message:
                    # The connection is only usable once we've received a
                    # message from the server (not on the connect event!!), so
                    # we wait to receive something before sending our first
                    # message
                    await sio.emit('dev_data', namespace=namespace)
                    self._received_message = True
                if not self._received_dev_data:
                    logging.debug("Dev data not received yet, ignoring update")
                    return
                if node_update_callback is not None:
                    node_update_callback(data)

        sio.register_namespace(SmartboxAPIV2Namespace(self, namespace))

        async def send_ping(interval):
            while True:
                await asyncio.sleep(interval)
                logging.debug("Sending ping")
                await sio.send('ping', namespace=namespace)

        sio.start_background_task(send_ping, 20)

        while True:
            encoded_token = urllib.parse.quote(self._access_token, safe='~()*!.\'')
            url = f"{self._api_host}:443/?token={self._access_token}&dev_id={device_id}"

            logging.debug(f"Connecting to {url}")
            await sio.connect(url, namespaces=[f"{namespace}?token={self._access_token}&dev_id={device_id}"])

            await sio.wait()
            self._check_refresh()

    def get_api_name(self):
        return self._api_name

    def get_access_token(self):
        return self._access_token

    def get_refresh_token(self):
        return self._refresh_token

    def get_expiry_time(self):
        return self._expires_at

    def get_devices(self):
        response = self._api_request("devs")
        return response['devs']

    def get_grouped_devices(self):
        response = self._api_request("grouped_devs")
        return response

    def get_nodes(self, device_id):
        response = self._api_request(f"devs/{device_id}/mgr/nodes")
        return response['nodes']

    def get_status(self, device_id, node):
        return self._api_request(f"devs/{device_id}/{node['type']}/{node['addr']}/status")

    def set_status(self, device_id, node, status_args):
        data = {k: v for k, v in status_args.items() if v is not None}
        if 'stemp' in data and 'units' not in data:
            raise ValueError("Must supply unit with temperature fields")
        return self._api_post(data=data, path=f"devs/{device_id}/{node['type']}/{node['addr']}/status")

    def get_setup(self, device_id, node):
        return self._api_request(f"devs/{device_id}/{node['type']}/{node['addr']}/setup")

    def set_setup(self, device_id, node, setup_args):
        data = {k: v for k, v in setup_args.items() if v is not None}
        # setup seems to require all settings to be re-posted, so get current
        # values and update
        setup_data = self.get_setup(device_id, node)
        setup_data.update(data)
        return self._api_post(data=setup_data, path=f"devs/{device_id}/{node['type']}/{node['addr']}/setup")

    def get_away_status(self, device_id):
        return self._api_request(f"devs/{device_id}/mgr/away_status")

    def set_away_status(self, device_id, status_args):
        data = {k: v for k, v in status_args.items() if v is not None}
        return self._api_post(data=data, path=f"devs/{device_id}/mgr/away_status")


@click.group(chain=True)
@click.option('-a', '--api-name', required=True, help='API name')
@click.option('-b', '--basic-auth-creds', required=True, help='API basic auth credentials')
@click.option('-u', '--username', required=True, help='API username')
@click.option('-p', '--password', required=True, help='API password')
@click.option('-v', '--verbose/--no-verbose', default=False, help='Enable verbose logging')
@click.pass_context
def smartbox(ctx, api_name, basic_auth_creds, username, password, verbose):
    ctx.ensure_object(dict)
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
                        level=logging.DEBUG if verbose else logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')
    session = Session(api_name, basic_auth_creds, username, password, verbose)
    ctx.obj['session'] = session


@smartbox.command(help='Show devices')
@click.pass_context
def devices(ctx):
    session = ctx.obj['session']
    devices = session.get_devices()
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(devices)


@smartbox.command(help='Show nodes')
@click.pass_context
def nodes(ctx):
    session = ctx.obj['session']
    devices = session.get_devices()
    pp = pprint.PrettyPrinter(indent=4)

    for device in devices:
        print(f"{device['name']} (dev_id: {device['dev_id']})")
        nodes = session.get_nodes(device['dev_id'])
        pp.pprint(nodes)


@smartbox.command(help='Show node status')
@click.pass_context
def status(ctx):
    session = ctx.obj['session']
    devices = session.get_devices()
    pp = pprint.PrettyPrinter(indent=4)

    for device in devices:
        print(f"{device['name']} (dev_id: {device['dev_id']})")
        nodes = session.get_nodes(device['dev_id'])

        for node in nodes:
            print(f"{node['name']} (addr: {node['addr']})")
            status = session.get_status(device['dev_id'], node)
            pp.pprint(status)


@smartbox.command(help='Set node status (pass settings as extra args, e.g. mode=auto)')
@click.option('-d', '--device-id', required=True, help='Device ID for node to set status on')
@click.option('-n', '--node-addr', type=int, required=True, help='Address of node to set status on')
@click.option('--locked', type=bool)
@click.option('--mode')
@click.option('--stemp')
@click.option('--units')
# TODO: other options
@click.pass_context
def set_status(ctx, device_id, node_addr, **kwargs):
    session = ctx.obj['session']
    devices = session.get_devices()
    device = next(d for d in devices if d['dev_id'] == device_id)
    nodes = session.get_nodes(device['dev_id'])
    node = next(n for n in nodes if n['addr'] == node_addr)

    session.set_status(device['dev_id'], node, kwargs)


@smartbox.command(help='Show node setup')
@click.pass_context
def setup(ctx):
    session = ctx.obj['session']
    devices = session.get_devices()
    pp = pprint.PrettyPrinter(indent=4)

    for device in devices:
        print(f"{device['name']} (dev_id: {device['dev_id']})")
        nodes = session.get_nodes(device['dev_id'])

        for node in nodes:
            print(f"{node['name']} (addr: {node['addr']})")
            setup = session.get_setup(device['dev_id'], node)
            pp.pprint(setup)


@smartbox.command(help='Set node setup (pass settings as extra args, e.g. mode=auto)')
@click.option('-d', '--device-id', required=True, help='Device ID for node to set setup on')
@click.option('-n', '--node-addr', type=int, required=True, help='Address of node to set setup on')
@click.option('--true-radiant-enabled', type=bool)
# TODO: other options
@click.pass_context
def set_setup(ctx, device_id, node_addr, **kwargs):
    session = ctx.obj['session']
    devices = session.get_devices()
    device = next(d for d in devices if d['dev_id'] == device_id)
    nodes = session.get_nodes(device['dev_id'])
    node = next(n for n in nodes if n['addr'] == node_addr)

    session.set_setup(device['dev_id'], node, kwargs)


@smartbox.command(help='Show node away_status')
@click.pass_context
def away_status(ctx):
    session = ctx.obj['session']
    devices = session.get_devices()
    pp = pprint.PrettyPrinter(indent=4)

    for device in devices:
        print(f"{device['name']} (dev_id: {device['dev_id']})")
        away_status = session.get_away_status(device['dev_id'])
        pp.pprint(away_status)


@smartbox.command(help='Set device away_status (pass settings as extra args, e.g. mode=auto)')
@click.option('-d', '--device-id', required=True, help='Device ID to set away_status on')
@click.option('--away', type=bool)
@click.option('--enabled', type=bool)
@click.option('--forced', type=bool)
@click.pass_context
def set_away_status(ctx, device_id, **kwargs):
    session = ctx.obj['session']
    devices = session.get_devices()
    device = next(d for d in devices if d['dev_id'] == device_id)

    session.set_away_status(device['dev_id'], kwargs)


@smartbox.command(
    help=
    'Open socket.io connection to device.  **Note: opening a session while another (e.g. web UI) is open does not work**'
)
@click.option('-d', '--device-id', required=True, help='Device ID to open socket for')
@click.pass_context
def socket(ctx, device_id):
    session = ctx.obj['session']
    pp = pprint.PrettyPrinter(indent=4)

    def on_dev_data(data):
        logging.info("Received dev_data:")
        pp.pprint(data)

    def on_update(data):
        logging.info("Received update:")
        pp.pprint(data)

    asyncio.run(session.open_socket(device_id, on_dev_data, on_update))

import click
import json
import logging
import pprint
import requests


class Session(object):
    def __init__(self, api_name, access_token, refresh_token, expires_in):
        self._api_name = api_name
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._expires_in = expires_in

    def _get_headers(self):
        # TODO: token refresh
        return {
            "Authorization": f"Bearer {self._access_token}",
            "content-type": "application/json",
        }

    def _api_request(self, path=""):
        api_url = f"https://api-{self._api_name}.helki.com/api/v2/devs{path}"
        response = requests.get(api_url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def _api_post(self, data, path=""):
        api_url = f"https://api-{self._api_name}.helki.com/api/v2/devs{path}"
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

    def get_api_name(self):
        return self._api_name

    def get_devices(self):
        response = self._api_request()
        return response['devs']

    def get_nodes(self, device_id):
        response = self._api_request(f"/{device_id}/mgr/nodes")
        return response['nodes']

    def get_status(self, device_id, node):
        return self._api_request(f"/{device_id}/{node['type']}/{node['addr']}/status")

    def set_status(self, device_id, node, status_args):
        data = {k: v for k, v in status_args.items() if v is not None}
        if 'stemp' in data and 'units' not in data:
            raise ValueError("Must supply unit with temperature fields")
        return self._api_post(data=data, path=f"/{device_id}/{node['type']}/{node['addr']}/status")

    def get_setup(self, device_id, node):
        return self._api_request(f"/{device_id}/{node['type']}/{node['addr']}/setup")

    def set_setup(self, device_id, node, setup_args):
        data = {k: v for k, v in setup_args.items() if v is not None}
        # setup seems to require all settings to be re-posted, so get current
        # values and update
        setup_data = self.get_setup(device_id, node)
        setup_data.update(data)
        return self._api_post(data=setup_data, path=f"/{device_id}/{node['type']}/{node['addr']}/setup")

    def get_away_status(self, device_id):
        return self._api_request(f"/{device_id}/mgr/away_status")

    def set_away_status(self, device_id, status_args):
        data = {k: v for k, v in status_args.items() if v is not None}
        return self._api_post(data=data, path=f"/{device_id}/mgr/away_status")


def get_session(api_name, basic_auth_credentials, username, password):
    token_data = f'grant_type=password&username={username}&password={password}'
    token_headers = {
        'authorization': f'Basic {basic_auth_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    token_url = f"https://api-{api_name}.helki.com/client/token"
    response = requests.post(token_url, data=token_data, headers=token_headers)
    r = response.json()
    if r['token_type'] != 'bearer':
        raise RuntimeError(f"Unsupported token type {r['token_type']}")
    return Session(api_name, r['access_token'], r['refresh_token'], r['expires_in'])


@click.group(chain=True)
@click.option('-a', '--api-name', required=True, help='API name')
@click.option('-b', '--basic-auth-creds', required=True, help='API basic auth credentials')
@click.option('-u', '--username', required=True, help='API username')
@click.option('-p', '--password', required=True, help='API password')
@click.option('-v', '--verbose/--no-verbose', default=False, help='Enable verbose logging')
@click.pass_context
def smartbox(ctx, api_name, basic_auth_creds, username, password, verbose):
    ctx.ensure_object(dict)
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    session = get_session(api_name, basic_auth_creds, username, password)
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

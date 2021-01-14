import pytest
import smartbox


def test_basic(requests_mock):
    api_name = 'myapi'
    basic_auth_creds = 'sldjfls93r2lkj'
    username = 'xxxxx'
    password = 'yyyyy'

    token_type = 'bearer'
    access_token = 'sj32oj2lkwjf'
    refresh_token = '23ij2oij324j3423'
    expires_in = 14400
    requests_mock.post(f"https://api-{api_name}.helki.com/client/token",
                       json={
                           'token_type': token_type,
                           'access_token': access_token,
                           'expires_in': expires_in,
                           'refresh_token': refresh_token,
                       })
    session = smartbox.get_session(api_name, basic_auth_creds, username, password)
    assert requests_mock.last_request.text == f'grant_type=password&username={username}&password={password}'
    assert requests_mock.last_request.headers['authorization'] == f"Basic {basic_auth_creds}"
    assert session.get_api_name() == api_name

    # devices
    dev_id = '2o3jo2jkj'
    dev_name = 'My device'
    requests_mock.get(f"https://api-{api_name}.helki.com/api/v2/devs",
                      json={'devs': [{
                          'dev_id': dev_id,
                          'name': dev_name,
                      }]})
    resp = session.get_devices()
    assert len(resp) == 1
    assert resp[0]['dev_id'] == dev_id
    assert resp[0]['name'] == dev_name

    # nodes
    node_1 = {'addr': 1, 'name': 'My heater', 'type': 'htr'}
    node_2 = {'addr': 2, 'name': 'My other heater', 'type': 'htr'}
    requests_mock.get(f"https://api-{api_name}.helki.com/api/v2/devs/{dev_id}/mgr/nodes",
                      json={'nodes': [node_1, node_2]})
    resp = session.get_nodes(dev_id)
    assert len(resp) == 2
    assert resp[0] == node_1
    assert resp[1] == node_2

    # status
    requests_mock.get(f"https://api-{api_name}.helki.com/api/v2/devs/{dev_id}/{node_1['type']}/{node_1['addr']}/status",
                      json={
                          'mode': 'auto',
                          'stemp': '16.0',
                          'mtemp': '19.2'
                      })
    resp = session.get_status(dev_id, node_1)
    assert resp['mode'] == 'auto'
    assert resp['stemp'] == '16.0'
    assert resp['mtemp'] == '19.2'

    with pytest.raises(ValueError):
        resp = session.set_status(dev_id, node_1, {'stemp': '17.0'})

    requests_mock.post(
        f"https://api-{api_name}.helki.com/api/v2/devs/{dev_id}/{node_1['type']}/{node_1['addr']}/status",
        json={
            'mode': 'auto',
            'stemp': '17.0',
            'mtemp': '19.2'
        })
    resp = session.set_status(dev_id, node_1, {'stemp': '17.0', 'units': 'C'})
    assert requests_mock.last_request.json() == {'stemp': '17.0', 'units': 'C'}

    # setup
    requests_mock.get(f"https://api-{api_name}.helki.com/api/v2/devs/{dev_id}/{node_2['type']}/{node_2['addr']}/setup",
                      json={
                          'away_mode': 0,
                          'units': 'C'
                      })
    resp = session.get_setup(dev_id, node_2)
    assert resp['away_mode'] == 0
    assert resp['units'] == 'C'

    requests_mock.post(f"https://api-{api_name}.helki.com/api/v2/devs/{dev_id}/{node_2['type']}/{node_2['addr']}/setup",
                       json={
                           'away_mode': 0,
                           'units': 'F'
                       })
    resp = session.set_setup(dev_id, node_2, {'units': 'F'})
    assert requests_mock.last_request.json() == {'away_mode': 0, 'units': 'F'}

    # away_status
    requests_mock.get(f"https://api-{api_name}.helki.com/api/v2/devs/{dev_id}/mgr/away_status",
                      json={
                          'away': False,
                          'enabled': True
                      })
    resp = session.get_away_status(dev_id)
    assert not resp['away']
    assert resp['enabled']

    requests_mock.post(f"https://api-{api_name}.helki.com/api/v2/devs/{dev_id}/mgr/away_status",
                       json={
                           'away': True,
                           'enabled': True
                       })
    resp = session.set_away_status(dev_id, {'away': True})
    assert requests_mock.last_request.json() == {'away': True}
    assert resp['away']
    assert resp['enabled']

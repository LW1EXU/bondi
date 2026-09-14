import json
from unittest.mock import patch
import httpx
import pytest
from agents.crawler import download, validate_url
from agents.models import Branch, Dataset, GazetteerEntry, Stop
from agents.normalizer import canonicalize, normalize, geojson
from agents.validator import diff, validate


def dataset():
    return Dataset(branches=[Branch(id='b', line_id='test', name='Fixture sintética', direction=0,
        variant='regular', stops=[
            Stop(id='a', canonical='7 y 50', lat=-34.913, lon=-57.948, source_url='https://example.org/a'),
            Stop(id='z', canonical='7 y 51', lat=-34.914, lon=-57.949, source_url='https://example.org/a')],
        unresolved=[], source_url='https://example.org/a', source_sha256='abc', evidence='fixture sintética')])


@pytest.mark.parametrize('raw,expected', [('Diag. 74 y 12','diagonal 74 y 12'),
    ('7 esquina 45','7 y 45'), ('Cno. Belgrano y 501','camino belgrano y 501'),
    (' Plaza   Paso ','plaza paso'), ('7 & 50','7 y 50')])
def test_addresses(raw, expected):
    assert canonicalize(raw) == expected


def test_anomalies():
    data = dataset()
    assert validate(data) == []
    data.branches[0].stops[1].lat = 0
    data.branches[0].unresolved = ['Diagonal desconocida']
    assert len(validate(data)) == 2
    assert validate(Dataset(branches=[]), dataset())


def test_semver():
    data = dataset()
    assert diff(None, data)['version'] == '0.1.0'
    assert diff(data, data, '0.1.0')['version'] == '0.1.0'
    changed = data.model_copy(deep=True)
    changed.branches[0].stops.reverse()
    assert diff(data, changed, '0.1.0')['version'] == '1.0.0'


def test_geojson_does_not_bridge_unresolved():
    data = dataset()
    assert geojson(data)['features'][0]['geometry']['coordinates'][0] == [-57.948, -34.913]
    data.branches[0].unresolved = ['missing']
    assert geojson(data)['features'] == []


def test_normalizer_uses_gazetteer_without_model():
    entry = GazetteerEntry(canonical='7 y 50', lat=-34.913, lon=-57.948, source_url='https://example.org/a')
    record = {'url':'https://example.org/a','sha256':'abc','extraction': {
        'branches':[{'line_id':'test','name':'fixture','direction':0,'stop_names':['7 y 50'], 'evidence':'solo una fixture'}], 'alerts':[]}}
    with patch('agents.normalizer.structured', side_effect=AssertionError('Model not needed')):
        result = normalize([record], [entry])
    assert result.branches[0].stops[0].lat == entry.lat
    assert result.branches[0].unresolved == []


def test_unknown_coordinates_remain_unresolved():
    from agents.models import Addresses, Address
    record = {'url':'https://example.org/a','sha256':'abc','extraction': {
        'branches':[{'line_id':'test','name':'fixture','direction':0,'stop_names':['Plaza X'], 'evidence':'solo una fixture'}], 'alerts':[]}}
    with patch('agents.normalizer.structured', return_value=Addresses(addresses=[Address(original='Plaza X',canonical='plaza x',kind='poi')])):
        result = normalize([record], [])
    assert result.branches[0].stops == []
    assert validate(result)


@pytest.mark.parametrize('url',['http://example.org', 'https://evil.org', 'https://user:pass@example.org'])
def test_source_allowlist(url):
    with pytest.raises(ValueError):
        validate_url(url, {'example.org'})


def test_private_network_rejected():
    with patch('socket.getaddrinfo', return_value=[(2,1,6,'',('127.0.0.1',443))]):
        with pytest.raises(ValueError):
            validate_url('https://example.org', {'example.org'})


def test_redirect_not_followed():
    transport = httpx.MockTransport(lambda request: httpx.Response(302, headers={'location':'http://127.0.0.1'}))
    with patch('agents.crawler.validate_url'), httpx.Client(transport=transport) as client:
        with pytest.raises(httpx.HTTPStatusError):
            download(client, 'https://example.org', {'example.org'})


def test_failed_run_keeps_previous(tmp_path, monkeypatch):
    from agents.worker import run_once
    monkeypatch.setenv('DATA_DIR',str(tmp_path))
    previous = tmp_path / 'published.json'
    previous.write_text('{"sentinel":true}')
    with pytest.raises(ValueError, match='No hay fuentes'):
        run_once()
    assert json.loads(previous.read_text()) == {'sentinel':True}
    assert json.loads(next(tmp_path.glob('runs/*/status.json')).read_text())['status'] == 'failed'

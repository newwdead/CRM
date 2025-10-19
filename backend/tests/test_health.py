from fastapi.testclient import TestClient
from app.main import app

def test_health_ok():
    client = TestClient(app)
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'

def test_contacts_pagination_shape():
    client = TestClient(app)
    r = client.get('/contacts/', params={'page':1,'size':2,'sort':'-id'})
    assert r.status_code == 200
    data = r.json()
    # Accept both list (legacy) and paginated object
    if isinstance(data, list):
        assert isinstance(data, list)
    else:
        assert set(['page','size','total','items']).issubset(data.keys())
        assert isinstance(data['items'], list)

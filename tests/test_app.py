import os, tempfile, pytest
from app import app, init_db, normalize_url

@pytest.fixture()
def client():
    fd,path=tempfile.mkstemp(); os.close(fd)
    app.config.update(TESTING=True,DATABASE=path)
    init_db()
    with app.test_client() as c: yield c
    os.unlink(path)

def test_home(client):
    r=client.get("/")
    assert r.status_code==200 and b"WebWatch" in r.data

def test_health(client):
    r=client.get("/health")
    assert r.status_code==200 and r.json["status"]=="ok"

def test_add_site(client):
    r=client.post("/add",data={"name":"Example","url":"example.com"},follow_redirects=True)
    assert r.status_code==200 and b"https://example.com" in r.data

def test_reject_bad_url(client):
    r=client.post("/add",data={"name":"Bad","url":"ftp://example.com"},follow_redirects=True)
    assert b"valid http or https" in r.data

def test_normalize_url():
    assert normalize_url("example.com")=="https://example.com"

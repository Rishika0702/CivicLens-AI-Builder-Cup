from fastapi.testclient import TestClient
from app.main import app, distance_km
client=TestClient(app)
def test_seed_clusters():
 s=client.get('/api/stats').json()
 assert s['reports']==50 and s['incidents']==5 and s['duplicates_merged']==45
def test_health():assert client.get('/health').status_code==200
def test_submit_merges():
 before=client.get('/api/stats').json()
 r=client.post('/api/reports',json={'description':'Pothole in road causing accidents','lat':17.4318,'lng':78.4071})
 assert r.status_code==201 and r.json()['duplicate']
 after=client.get('/api/stats').json()
 assert after['incidents']==before['incidents'] and after['reports']==before['reports']+1
def test_separation():assert distance_km(17.43,78.4,18.0,78.4)>50
def test_status_requires_auth():assert client.patch('/api/incidents/INC-001',json={'status':'Resolved'}).status_code==401

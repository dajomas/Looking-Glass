import pytest
from looking_glass.db import Database
from looking_glass.services.campaign_search import search_campaign,inspect_target,target_url

@pytest.fixture
def db(tmp_path):
    db=Database(tmp_path/'search.db');db.migrate()
    with db.connect() as c:
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'Adventure'),(2,'Private')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'Crypt','a.png',400,200),(2,2,'Private','b.png',400,200)")
        c.execute("INSERT INTO room_notes VALUES(1,'key',100,100,'Throne Room','A silver key beneath the throne. Straße.',1)")
        c.execute("INSERT INTO room_notes VALUES(1,'unnamed',50,50,'','Unmarked treasure vault',1)")
        c.execute("INSERT INTO map_transitions(id,map_id,name,player_label,notes,kind,x,y,visibility,availability) VALUES('stairs',1,'Downstairs','Lower floor','Silver ladder','stairs',20,30,'secret','usable')")
        c.execute("INSERT INTO imported_room_notes(map_id,name,markdown,digest) VALUES(1,'Library room','Unassigned silver statue','digest')")
        c.execute("INSERT INTO room_notes VALUES(2,'private',1,1,'Silver secret','Never disclose',1)")
    return db

def run(db,q,kind='all',limit=50):
    with db.connect() as c:
        c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
        return search_campaign(c,1,q,kind,limit)

@pytest.mark.parametrize('query,kind', [('Crypt','map'),('throne','room'),('treasure','room'),('lower floor','passage'),('statue','library')])
def test_categories(db,query,kind):
    result=run(db,query,kind)
    assert result['results'] and all(r['kind']==kind for r in result['results'])

def test_scope_unicode_and_words(db):
    assert run(db,'STRASSE')['results'][0]['title']=='Throne Room'
    assert len(run(db,'silver crypt')['results'])==3
    assert not run(db,'never disclose')['results']
    assert not run(db,'silver missingword')['results']

@pytest.mark.parametrize('query',["' OR 1=1 --",'%','_','*'])
def test_literal_queries(db,query):assert not run(db,query)['results']

def test_blank_and_limits(db):
    assert not run(db,'   ')['results']
    result=run(db,'crypt',limit=2)
    assert len(result['results'])==2 and result['truncated']
    assert run(db,'crypt')['results'][0]['kind']=='map'
    with pytest.raises(ValueError):run(db,'x'*201)
    with pytest.raises(ValueError):run(db,'x','invalid')

def test_inspect_target_and_urls(db):
    with db.connect() as c:
        assert inspect_target(c,1,'room','key')['x']==100
        assert inspect_target(c,1,'passage','stairs')['markdown']=='Silver ladder'
        assert 'x' not in inspect_target(c,1,'library','1')
        with pytest.raises(LookupError):inspect_target(c,1,'room','private')
        c.execute("DELETE FROM room_notes WHERE area_key='key'")
        with pytest.raises(LookupError):inspect_target(c,1,'room','key')
    assert 'key=a%26b' in target_url(1,1,'room','a&b')

def test_readonly_and_snippet_bound(db):
    with db.connect() as c:
        c.execute("UPDATE room_notes SET markdown=? WHERE area_key='key'",('secret '*1000,))
        before='\n'.join(c.iterdump())
    result=run(db,'secret')
    assert all(len(r['snippet'])<=222 for r in result['results'])
    with db.connect() as c:assert '\n'.join(c.iterdump())==before
    assert all('/inspect/maps/1' in r['url'] for r in result['results'])

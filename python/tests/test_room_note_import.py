import sqlite3
import pytest
from looking_glass.db import Database
from looking_glass.services.room_note_import import parse, store, list_entries, ImportError, MAX_BYTES


def test_sections_preserve_markdown_and_subheadings():
    result=parse(b"Intro\n\n## Crypt\n**Gold**\n\n### Trap\nBeware\n\n## Hall\n- bones\n")
    assert result["level"]==2 and result["ignored_preamble"]
    assert [e["name"] for e in result["entries"]]==["Crypt","Hall"]
    assert result["entries"][0]["markdown"]=="**Gold**\n\n### Trap\nBeware"


def test_code_quotes_lists_not_room_headings():
    result=parse(b"## Crypt\n```md\n# not a room\n```\n> # quote\n\n- item\n  # nested\n\n## Hall\n")
    assert result["level"]==2
    assert len(result["entries"])==2
    assert "# not a room" in result["entries"][0]["markdown"]


def test_setext_bom_crlf_inline_and_empty_note():
    result=parse("\ufeff**Crypt**\r\n========\r\nBody\r\n\r\nHall\r\n====\r\n".encode())
    assert [(e["name"],e["markdown"]) for e in result["entries"]]==[("Crypt","Body"),("Hall","")]


def test_highest_present_is_global_not_first():
    result=parse(b"### preamble\nIgnored\n# A\n## Detail\ntext\n# B\n")
    assert result["level"]==1 and result["ignored_preamble"]
    assert [e["name"] for e in result["entries"]]==["A","B"]


@pytest.mark.parametrize("raw", [b"no headings",b"# \ntext",b"\xff",b"# A\n\x00",b"x"*(MAX_BYTES+1),b"# "+b"a"*201,b"# A\n"+b"a"*100001])
def test_invalid_imports(raw):
    with pytest.raises(ImportError): parse(raw)


def test_duplicate_titles_and_idempotent_append(tmp_path):
    db=Database(tmp_path/"db.sqlite");v=db.migrate();assert db.migrate()==v
    with db.connect() as conn:
        conn.execute("INSERT INTO campaigns(id,name) VALUES(1,'Test')")
        conn.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(99,1,'Map','map.png',400,200)")
        entries=parse(b"# A\nfirst\n# A\nsecond\n")["entries"]
        assert store(conn,99,entries)==2
        assert store(conn,99,entries)==0
        rows=list_entries(conn,99)
        assert len(rows)==2 and rows[0]["id"]!=rows[1]["id"]
        assert list_entries(conn,100)==[]
        conn.execute("DELETE FROM maps WHERE id=99")
        assert list_entries(conn,99)==[]

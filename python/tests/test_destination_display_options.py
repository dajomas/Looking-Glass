"""Execute the real route body with stub dependencies (no FastAPI needed)."""
import ast
import asyncio
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import pytest

@pytest.mark.parametrize("active,saved,live,restorable,current",[(False,[],["reveal"],False,True),(False,["reveal"],[],True,False),(True,[],["reveal"],True,True),(False,[],[],False,False)])
def test_saved_and_current_reveals_are_independent(active,saved,live,restorable,current):
    source=Path(__file__).parents[1]/"looking_glass/web/admin/display_options.py"
    tree=ast.parse(source.read_text());fn=next(n for n in ast.walk(tree) if isinstance(n,ast.AsyncFunctionDef) and n.name=="display_options")
    fn.decorator_list=[];fn.returns=None
    for a in fn.args.args:a.annotation=None
    @contextmanager
    def connect():yield object()
    ns=dict(asyncio=asyncio,map_for_manage=lambda c,u,mid:({},dict(active_map_id=2 if active else 1)),
        fog_inputs=lambda *a:(None,[],live),checkpoint_operations=lambda *a:saved,
        has_restorable_reveals=lambda engine,spec,segs,ops:bool(ops),BadRequest=ValueError,
        JSONResponse=lambda data,**kw:data)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(source),"exec"),ns)
    ctx=SimpleNamespace(db=SimpleNamespace(connect=connect),fog=None)
    result=asyncio.run(ns["display_options"](ctx,{},2))
    assert result["can_restore"]==restorable and result["has_current_reveals"]==current

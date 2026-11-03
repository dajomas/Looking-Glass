"""Campaign session-checkpoint UI. GETs inspect; CSRF-protected POSTs change state."""
import asyncio
import sqlite3
from typing import Annotated
from fastapi import APIRouter, Form, Query, Request
from ...services import session_checkpoints as checkpoints
from ..access import campaign_for_manage
from ..deps import CtxDep, UserDep, CsrfUserDep, NotFound
from ..templating import render
from .campaigns import _back
from . import notify

router=APIRouter()


def _get(conn,cid,checkpoint_id):
    try:return checkpoints.get(conn,cid,checkpoint_id)
    except LookupError as exc:raise NotFound(str(exc)) from exc


def _page(request,template,**context):
    response=render(request,template,**context)
    response.headers['Cache-Control']='no-store'
    return response


@router.get('/campaigns/{campaign_id}/checkpoints')
def checkpoint_list(request:Request,ctx:CtxDep,user:UserDep,campaign_id:int,
                    page:Annotated[int,Query(ge=1,le=1000000)]=1):
    with ctx.db.connect() as conn:
        conn.execute('PRAGMA query_only=ON');conn.execute('BEGIN')
        campaign=campaign_for_manage(conn,user,campaign_id)
        saved=conn.execute('SELECT id,name,notes,automatic,created_at FROM campaign_checkpoints WHERE campaign_id=? ORDER BY id DESC LIMIT 51 OFFSET ?',(campaign_id,(page-1)*50)).fetchall()
    return _page(request,'admin/session_checkpoints.html',campaign=campaign,checkpoints=saved[:50],has_more=len(saved)>50,page=page)


@router.get('/campaigns/{campaign_id}/checkpoints/{checkpoint_id}')
def checkpoint_preview(request:Request,ctx:CtxDep,user:UserDep,campaign_id:int,checkpoint_id:int):
    with ctx.db.connect() as conn:
        conn.execute('PRAGMA query_only=ON');conn.execute('BEGIN')
        campaign=campaign_for_manage(conn,user,campaign_id)
        saved=_get(conn,campaign_id,checkpoint_id)
        view=None;problem=None
        try:view=checkpoints.preview(conn,campaign_id,checkpoint_id,ctx.settings.maps_dir,ctx.settings.section('fog'))
        except OSError:problem='Current map images could not be read. Check storage before previewing or restoring.'
        except (ValueError,KeyError,TypeError):problem='Checkpoint data or current campaign state could not be validated. Restore is blocked.'
    return _page(request,'admin/session_checkpoint_preview.html',campaign=campaign,checkpoint=saved,view=view,problem=problem)


@router.post('/campaigns/{campaign_id}/checkpoints')
def checkpoint_create(ctx:CtxDep,user:CsrfUserDep,campaign_id:int,
                      name:Annotated[str,Form(min_length=1,max_length=120)],
                      notes:Annotated[str,Form(max_length=2000)]=''):
    try:
        with ctx.db.connect() as conn:
            conn.execute('BEGIN IMMEDIATE');campaign_for_manage(conn,user,campaign_id)
            checkpoints.create(conn,campaign_id,name,notes,ctx.settings.maps_dir,ctx.settings.section('fog'),user['id'])
    except OSError:return _back(f'/campaigns/{campaign_id}/checkpoints',err='Checkpoint could not read map images. Check storage; nothing was saved.')
    except (ValueError,KeyError,TypeError):return _back(f'/campaigns/{campaign_id}/checkpoints',err='Checkpoint could not validate campaign state or name. Nothing was saved.')
    return _back(f'/campaigns/{campaign_id}/checkpoints',ok='Session checkpoint saved. Player display unchanged.')


@router.post('/campaigns/{campaign_id}/checkpoints/{checkpoint_id}/restore')
async def checkpoint_restore(ctx:CtxDep,user:CsrfUserDep,campaign_id:int,checkpoint_id:int,
                             token:Annotated[str,Form(max_length=64)]='',
                             confirm:Annotated[str,Form(max_length=120)]=''):
    path=f'/campaigns/{campaign_id}/checkpoints/{checkpoint_id}'
    def apply_restore():
        with ctx.db.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            campaign=campaign_for_manage(conn,user,campaign_id);_get(conn,campaign_id,checkpoint_id)
            if confirm.strip()!=campaign['name']:
                raise ValueError('Type the current campaign name to confirm restore.')
            return checkpoints.restore(conn,campaign_id,checkpoint_id,ctx.settings.maps_dir,ctx.settings.section('fog'),user['id'],token)
    try:
        safety,mids=await asyncio.to_thread(apply_restore)
    except OSError:return _back(path,err='Map images could not be read. No state was restored.')
    except ValueError as exc:return _back(path,err=str(exc))
    except (KeyError,TypeError,sqlite3.IntegrityError):return _back(path,err='Invalid checkpoint state. Restore and safety save were rolled back.')
    for mid in mids:
        try:await asyncio.to_thread(ctx.fog.invalidate,mid)
        except OSError:pass  # Monotonic versions also prevent old cache reuse.
    await notify.campaign_changed(ctx,campaign_id,'session-checkpoint')
    return _back(f'/campaigns/{campaign_id}/checkpoints',ok=f'Session state restored. Automatic safety checkpoint #{safety} saved.')


@router.post('/campaigns/{campaign_id}/checkpoints/{checkpoint_id}/delete')
def checkpoint_delete(ctx:CtxDep,user:CsrfUserDep,campaign_id:int,checkpoint_id:int,
                      confirm:Annotated[str,Form(max_length=120)]=''):
    with ctx.db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE');campaign_for_manage(conn,user,campaign_id)
        saved=_get(conn,campaign_id,checkpoint_id)
        if confirm.strip()!=saved['name']:
            return _back(f'/campaigns/{campaign_id}/checkpoints/{checkpoint_id}',err='Type the checkpoint name to confirm deletion.')
        conn.execute('DELETE FROM campaign_checkpoints WHERE campaign_id=? AND id=?',(campaign_id,checkpoint_id))
    return _back(f'/campaigns/{campaign_id}/checkpoints',ok='Checkpoint deleted. Campaign play state unchanged.')

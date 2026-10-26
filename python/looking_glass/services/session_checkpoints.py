"""Named, campaign-scoped play-state snapshots. Callers own access and transactions."""
import hashlib
import json
import math
from .campaign_readiness import image_path

MAX_BYTES = 64 * 1024 * 1024
FORMAT = 1


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def get(conn,cid,checkpoint_id):
    row=conn.execute("SELECT * FROM campaign_checkpoints WHERE campaign_id=? AND id=?",(cid,checkpoint_id)).fetchone()
    if row is None:raise LookupError("Checkpoint not found in this campaign.")
    return row


def rows(conn,sql,args):
    return [dict(r) for r in conn.execute(sql,args)]


def capture(conn,cid,maps_dir,fog_config):
    campaign=conn.execute("SELECT active_map_id,session_version FROM campaigns WHERE id=?",(cid,)).fetchone()
    if campaign is None:raise LookupError("Campaign not found.")
    data=dict(version=FORMAT,campaign_id=cid,config=dict(fog_config),active_map_id=campaign[0],generation=campaign[1],maps=[])
    for m in conn.execute("SELECT * FROM maps WHERE campaign_id=? ORDER BY id",(cid,)):
        path=image_path(maps_dir,m['image_file'])
        with path.open('rb') as image: image_hash=hashlib.file_digest(image,'sha256').hexdigest()
        authored={k:m[k] for k in ('id','cache_token','image_file','width','height','wall_offset_x','wall_offset_y','wall_scale_x','wall_scale_y','doors_block')}
        authored['image_sha256']=image_hash
        authored['walls']=rows(conn,"SELECT id,x1,y1,x2,y2,kind,blocks,passage FROM walls WHERE map_id=? ORDER BY id",(m['id'],))
        authored['boundary_settings']=rows(conn,"SELECT disabled_types FROM map_wall_type_settings WHERE map_id=?",(m['id'],))
        authored['transitions']=rows(conn,"SELECT id,kind,x,y,visibility,availability,destination_id,link_defined,arrival FROM map_transitions WHERE map_id=? ORDER BY id",(m['id'],))
        snapshot=conn.execute("SELECT operations FROM map_fog_snapshots WHERE map_id=?",(m['id'],)).fetchone()
        data['maps'].append(dict(id=m['id'],name=m['name'],fingerprint=digest(authored),
            versions=[m['walls_version'],m['fog_version']],
            fog=rows(conn,"SELECT op,x,y FROM fog_ops WHERE map_id=? ORDER BY id",(m['id'],)),
            displayed=json.loads(snapshot[0]) if snapshot else None,
            doors=rows(conn,"SELECT r.wall_id,r.kind FROM door_runtime_states r JOIN walls w ON w.id=r.wall_id WHERE w.map_id=? ORDER BY r.wall_id",(m['id'],)),
            passages=rows(conn,"SELECT r.wall_id,r.side,r.kind FROM passage_runtime_states r JOIN walls w ON w.id=r.wall_id WHERE w.map_id=? ORDER BY r.wall_id,r.side",(m['id'],)),
            transitions=rows(conn,"SELECT id,runtime_visibility,runtime_availability,revision FROM map_transitions WHERE map_id=? ORDER BY id",(m['id'],))))
    if data['active_map_id'] is not None and data['active_map_id'] not in {m['id'] for m in data['maps']}:
        raise ValueError("Active map does not belong to this campaign.")
    for saved_map in data['maps']:
        validate_ops(saved_map['fog'])
        if saved_map['displayed'] is not None:validate_ops(saved_map['displayed'])
    if len(encode(data).encode())>MAX_BYTES:raise ValueError("Checkpoint exceeds the 64 MiB payload limit.")
    return data


def store(conn,cid,name,notes,data,user_id,automatic=False):
    name=name.strip()
    if not 1<=len(name)<=120 or len(notes)>2000:raise ValueError("Use a name of 1–120 characters and notes up to 2000 characters.")
    payload=encode(data)
    if len(payload.encode())>MAX_BYTES:raise ValueError("Checkpoint exceeds the 64 MiB payload limit.")
    return conn.execute("INSERT INTO campaign_checkpoints(campaign_id,name,notes,payload,created_by,automatic) VALUES(?,?,?,?,?,?)",(cid,name,notes,payload,user_id,int(automatic))).lastrowid


def create(conn,cid,name,notes,maps_dir,fog_config,user_id):
    return store(conn,cid,name,notes,capture(conn,cid,maps_dir,fog_config),user_id)


def decode(row):
    try:
        if len(row['payload'].encode())>MAX_BYTES:raise ValueError()
        data=json.loads(row['payload'])
        if data['version']!=FORMAT or data['campaign_id']!=row['campaign_id'] or not isinstance(data['maps'],list):raise ValueError()
        return data
    except (ValueError,KeyError,TypeError) as exc:raise ValueError("Checkpoint data is invalid or unsupported.") from exc


def validate_ops(ops):
    if not isinstance(ops,list):raise ValueError("Invalid checkpoint fog operations.")
    for op in ops:
        if not isinstance(op,dict) or set(op)!={'op','x','y'} or op['op'] not in ('reveal','hide','reveal_all','hide_all'):
            raise ValueError("Invalid checkpoint fog operation.")
        for key in ('x','y'):
            value=op[key]
            if value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value)):
                raise ValueError("Invalid checkpoint coordinate.")
            if value is None and op['op'] in ('reveal','hide'):raise ValueError("Missing checkpoint coordinate.")


def conflicts(target,current):
    problems=[]
    if target['config']!=current['config']:problems.append('Fog engine configuration has changed.')
    old={m['id']:m for m in target['maps']};now={m['id']:m for m in current['maps']}
    if len(old)!=len(target['maps']):raise ValueError('Duplicate checkpoint map identity.')
    if set(old)!=set(now):problems.append('Campaign map set has changed (added or removed maps).')
    for mid in sorted(set(old)&set(now)):
        if old[mid]['fingerprint']!=now[mid]['fingerprint']:
            problems.append(f"Map '{now[mid]['name']}' has changed image, geometry, boundary settings or authored passage configuration.")
    return problems


def preview(conn,cid,checkpoint_id,maps_dir,fog_config):
    row=get(conn,cid,checkpoint_id);target=decode(row);current=capture(conn,cid,maps_dir,fog_config)
    try:
        problems=conflicts(target,current)
        for m in target['maps']:
            validate_ops(m['fog'])
            if m['displayed'] is not None:validate_ops(m['displayed'])
        if target['active_map_id'] is not None and target['active_map_id'] not in {m['id'] for m in target['maps']}:
            raise ValueError('Invalid saved active map.')
    except (KeyError,TypeError) as exc:raise ValueError('Invalid checkpoint structure.') from exc
    token=digest(dict(target=row['payload'],current=current))
    return dict(checkpoint=row,target=target,current=current,conflicts=problems,token=token)


def restore(conn,cid,checkpoint_id,maps_dir,fog_config,user_id,expected_token):
    """Must run under BEGIN IMMEDIATE. Safety save and state changes are one savepoint."""
    view=preview(conn,cid,checkpoint_id,maps_dir,fog_config)
    if view['conflicts']:raise ValueError('Checkpoint is incompatible: '+ ' '.join(view['conflicts']))
    if not expected_token or expected_token!=view['token']:raise ValueError('Campaign state changed after preview. Review the checkpoint again.')
    target=view['target']
    conn.execute('SAVEPOINT restore_session_checkpoint')
    try:
        safety=store(conn,cid,('Automatic before restore: '+view['checkpoint']['name'])[:120],f"Safety checkpoint before restoring checkpoint {checkpoint_id}.",view['current'],user_id,True)
        for m in target['maps']:
            mid=m['id']
            conn.execute('DELETE FROM fog_ops WHERE map_id=?',(mid,))
            for op in m['fog']:
                conn.execute('INSERT INTO fog_ops(map_id,op,x,y,created_by) VALUES(?,?,?,?,?)',(mid,op['op'],op['x'],op['y'],user_id))
            conn.execute('DELETE FROM map_fog_snapshots WHERE map_id=?',(mid,))
            if m['displayed'] is not None:
                conn.execute('INSERT INTO map_fog_snapshots(map_id,operations) VALUES(?,?)',(mid,encode(m['displayed'])))
            # Fog hide_all triggers run before restoring runtime overrides.
            wall_ids={r[0] for r in conn.execute('SELECT id FROM walls WHERE map_id=?',(mid,))}
            conn.execute('DELETE FROM door_runtime_states WHERE wall_id IN (SELECT id FROM walls WHERE map_id=?)',(mid,))
            conn.execute('DELETE FROM passage_runtime_states WHERE wall_id IN (SELECT id FROM walls WHERE map_id=?)',(mid,))
            for r in m['doors']:
                if r['wall_id'] not in wall_ids:raise ValueError('Checkpoint door belongs to a different map.')
                conn.execute('INSERT INTO door_runtime_states(wall_id,kind) VALUES(?,?)',(r['wall_id'],r['kind']))
            for r in m['passages']:
                if r['wall_id'] not in wall_ids:raise ValueError('Checkpoint passage belongs to a different map.')
                conn.execute('INSERT INTO passage_runtime_states(wall_id,side,kind) VALUES(?,?,?)',(r['wall_id'],r['side'],r['kind']))
            ids={r[0] for r in conn.execute('SELECT id FROM map_transitions WHERE map_id=?',(mid,))}
            if {r['id'] for r in m['transitions']}!=ids or len(m['transitions'])!=len(ids):raise ValueError('Checkpoint transition identities do not match.')
            for r in m['transitions']:
                conn.execute('UPDATE map_transitions SET runtime_visibility=?,runtime_availability=?,revision=revision+1 WHERE map_id=? AND id=?',(r['runtime_visibility'],r['runtime_availability'],mid,r['id']))
            conn.execute('UPDATE maps SET walls_version=walls_version+1,fog_version=fog_version+1 WHERE id=?',(mid,))
        conn.execute('UPDATE campaigns SET active_map_id=?,session_version=session_version+1 WHERE id=?',(target['active_map_id'],cid))
        conn.execute('DELETE FROM map_transition_travel WHERE campaign_id=?',(cid,))
        conn.execute('RELEASE restore_session_checkpoint')
    except BaseException:
        conn.execute('ROLLBACK TO restore_session_checkpoint');conn.execute('RELEASE restore_session_checkpoint');raise
    return safety,[m['id'] for m in target['maps']]

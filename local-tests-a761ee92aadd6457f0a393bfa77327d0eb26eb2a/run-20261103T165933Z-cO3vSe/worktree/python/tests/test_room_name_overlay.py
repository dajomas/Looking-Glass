import io
from types import SimpleNamespace
import numpy as np
from PIL import Image
from looking_glass.services.room_notes import area_key, name_status_png


def test_named_and_unnamed_saved_geometry_only():
    labels=np.array([[1,1,0,2,2],[1,1,0,2,2],[0,0,0,0,0],[3,3,0,4,4]],dtype=np.int32)
    area=SimpleNamespace(labels=labels,count=4,shape=labels.shape,scale=1.0,region_signatures={})
    row=lambda label,x,y,name:{'area_key':area_key(area,label,5,4),'x':x,'y':y,'name':name}
    rows=[row(1,0,0,'Crypt'),row(2,3,0,'   '),row(3,0,3,'Hall')]
    # Detached record at a real region, and an out-of-image record, must not name it.
    rows+=[{'area_key':'old','x':3,'y':3,'name':'Stale'},dict(rows[0],x=99)]
    before=labels.copy()
    png,named,unnamed=name_status_png(area,rows,5,4)
    rgba=np.asarray(Image.open(io.BytesIO(png)))
    assert (named,unnamed)==(2,2)
    assert tuple(rgba[0,0])==(46,204,113,90)
    assert tuple(rgba[3,0])==(46,204,113,90)
    assert tuple(rgba[0,3])==(231,76,60,90)
    assert tuple(rgba[3,3])==(231,76,60,90)
    assert rgba[0,2,3]==0
    assert np.array_equal(before,labels)
    cleared=[dict(r,name='') for r in rows]
    assert name_status_png(area,cleared,5,4)[1:]==(0,4)

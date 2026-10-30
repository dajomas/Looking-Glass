## Editor paint policy and background-test isolation

Both editor stages share the `.stage` rule in `static/css/admin.css`; f4d60c3
already removes persistent `will-change: transform` while retaining transform
origin and PanZoom transforms. The supplied local run passes both wall-width
parameters, but the portal zoom-2.5 edge pixel still fails. Therefore removal of
stage promotion alone must not be described as a confirmed fix for that pixel.
A specific compositor or font-renderer root cause remains unproven.

The follow-up isolates the browser test's background-fill measurement from text
and border paint with temporary screenshot-only styles. Normal label geometry,
layering and interaction remain independently checked. Missing/white fill
negative controls check that the isolated probe still detects bad paint. The
normal final composited edge pixel is no longer the asserted paint location.

This follow-up changes tests and documentation only. It makes no additional
production CSS/JavaScript, API, database, authorization or dependency changes.


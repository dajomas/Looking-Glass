## Viewer framing

On each map/fog version change, the viewer fits and centers the bounding box of
all currently revealed pixels with a small margin. It does not reveal additional
pixels or send raw walls/images. With no revealed pixels it fits the full fogged
map. Manual pan/zoom works until the next update; Fit and resize frame the current
revealed region. With separated visible rooms it fits their combined extent,
not just the most recently clicked room.


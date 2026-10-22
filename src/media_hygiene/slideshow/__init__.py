"""`slideshow`: photos on the TV, the phone choosing the next one (0291).

One server on the PC, two pages: the screen (`/screen`, opened once in the TV's or the
Chromecast's browser: one photo, black borders, never a name) and the remote (`/`, on
the phone paired by `mh --lan`'s code, or on the PC). The server holds the show
(`show`): the selection, the photo shown, the timer; a TV reloaded or a phone gone to
sleep loses nothing. The TV is paired the other way round (`screens`): it shows a
short code, the paired phone types it. Read-only: the photos are never changed.
"""

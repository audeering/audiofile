# Test files

## Non SND format audio test files

This folder contains files to test file formats
that cannot be stored with `audiofile.write()`
and can hence not been created on the fly.

The files stored here are downloaded from
https://docs.espressif.com/projects/esp-adf/en/latest/design-guide/audio-samples.html.
They are excerpts
from "Furious Freak"
and "Galway",
Kevin MacLeod (incompetech.com),
licensed under Creative Commons:
[CC-BY-3.0](http://creativecommons.org/licenses/by/3.0/).

We converted the file `gs-16b-1c-44100hz.opus`
(which was stored wrongly with 48000 Hz)
to `gs-16b-1c-16000hz.opus` using
```bash
ffmpeg -y -i gs-16b-1c-44100hz.opus -ac 1 -ar 16000 gs-16b-1c-16000hz-fixed.opus
```

## Video test files

The folder contains the video file `video.mp4`,
which is a short excerpt from "Big Bunny"
from Blender Foundation | www.blender.org,
licensed under Creative Commons:
[CC-BY-3.0](http://creativecommons.org/licenses/by/3.0/).

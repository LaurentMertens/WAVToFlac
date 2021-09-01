# WAVToFlac

This package allows to easily copy an entire folder structure
containing music in WAV format to an identical folder structure
containing the same music in FLAC format.

Other filetypes, which can be specified, will simply be copied.
Everything else (neither WAV nor a specified filetype) will
simply be ignored.

Very handy to synchronize, e.g., an HD/Hi-Res music library on
a hard disk with a library on an SD card used in an HD/Hi-Res
music player.

The inverse operation is also possible: convert a FLAC library
to WAV (say, purely hypothetically speaking, in case your
external HD crashed).

Usage example:
```
    w2f = WAVToFlac()
    w2f.parse_dir_convert(path_in=PATH_IN, path_out=PATH_OUT, to_copy={'mp3', 'flac', 'jpg', 'jpeg', 'png'})
```

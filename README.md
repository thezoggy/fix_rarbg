# fix_rarbg
Clean up RARBG watermarks

## Overview

After backing up an old computer I stumbled upon this and figured someone else may benefit.
Several years ago I made this quick script to clean up RARBG "watermarks" (covers attachments and ads in subs).


## Requirements

* Requires python 2.7+ (not 3.x).

* Requires MKVToolNix to be installed (mkvmerge + mkvextract are used).


## Usage

By default it does dry run, to actaully do the clean up you need pass "--no-test-run"

```
usage: clean.py [-h] [-l | --no-log] [-d DIR] [-t | --no-test-run]
                [-p | --no-preserve-timestamp] [-m MKVMERGE_BIN]
                [-e MKVEXTRACT_BIN] [-v]

Clean up RARBG subs and removes attachments from MKV files.

optional arguments:
  -h, --help            show this help message and exit
  -l, --log             Create log file.
  --no-log              Do not create log file.
  -d DIR, --dir DIR     Pass file or folder to process
  -t, --test-run        Do not perform actions on files.
  --no-test-run         Perform actions on files.
  -p, --preserve-timestamp
                        Use source timestamp for remux file.
  --no-preserve-timestamp
                        Do not use source timestamp for remux file.
  -m MKVMERGE_BIN, --mkvmerge-bin MKVMERGE_BIN
                        Path to mkvmerge binary.
  -e MKVEXTRACT_BIN, --mkvextract-bin MKVEXTRACT_BIN
                        Path to mkvextract binary.
  -v, --verbose         Be verbose with output.
  ```


`python clean.py`

Will check the .mkv files in the same directory of the script.

You can specify a file or folder (recurisvely) to process:

`python clean.py -d "D:\TV"`


### Workflow

1) **Analyzing file/folder**

  See if RARBG is found in container title or filename.
  If there are jpeg attachments, assume file has not been sanitized.
  This allows you to blindly run this on folders or downloads as a post-processing job.

2) **Subs**

  Look for SRT subs, extract and delete lines with RARBG in them.

3) **Remux**

  Drop attachments, remux with cleaned subs.

4) **Cleanup**

  By default, the file timestamp is preserved from original file.


#### Notes

Looking at mkv file that needs to be cleaned:

```
mkvmerge.exe -i file.mkv
File 'file.mkv': container: Matroska
Track ID 0: video (MPEG-4p10/AVC/h.264)
Track ID 1: audio (AC-3/E-AC-3)
Track ID 2: subtitles (SubRip/SRT)
Track ID 3: subtitles (SubRip/SRT)
Attachment ID 1: type 'image/jpeg', size 5037 bytes, file name 'small_cover.jpg'
Attachment ID 2: type 'image/jpeg', size 8562 bytes, file name 'small_cover_land.jpg'
Attachment ID 3: type 'image/jpeg', size 23754 bytes, file name 'cover.jpg'
Attachment ID 4: type 'image/jpeg', size 24552 bytes, file name 'cover_land.jpg'
```

Dropping attachments is trivial:

```
mkvpropedit file.mkv --delete-attachment mime-type:image/jpeg
```
> Updates file inline instantly. Does not remux file, so original encoding info/date is still present. Does not reclaim space.

```
mkvmerge file.mkv --no-attachments -o output.mkv
```
> Takes a moment due to remux. Does reclaim space, but will have new encode date.

To cleanup the subs however takes a little more work as you ahve to extract, clean, then remux.


#### Sample Run

Sample run of processing single file (file name truncated):

```
D:\rarbg>python clean.py --no-test-run -v -d "S:\TV\Better Call Saul\Season 03\Better.Call.Saul.S03E04.mkv"
[ 2017-06-25 02:09:36 AM ]  Log file opened at D:\rarbg\log_20170625-020936.log
[ 2017-06-25 02:09:36 AM ]  --
[ 2017-06-25 02:09:36 AM ]  Running clean.py with configuration:
[ 2017-06-25 02:09:36 AM ]  MKVMERGE_BIN = C:\Program Files\MKVToolNix\mkvmerge.exe
[ 2017-06-25 02:09:36 AM ]  MKVEXTRACT_BIN = C:\Program Files\MKVToolNix\mkvextract.exe
[ 2017-06-25 02:09:36 AM ]  DIR = S:\TV\Better Call Saul\Season 03\Better.Call.Saul.S03E04.mkv
[ 2017-06-25 02:09:36 AM ]  DRY_RUN = False
[ 2017-06-25 02:09:36 AM ]  PRESERVE_TIMESTAMP = True
[ 2017-06-25 02:09:36 AM ]  VERBOSE = True
[ 2017-06-25 02:09:36 AM ]  --
[ 2017-06-25 02:09:36 AM ]  Analyzing 1 videos
[ 2017-06-25 02:09:36 AM ]  ==========================================
[ 2017-06-25 02:09:36 AM ]  Identifying video (1/1)
[ 2017-06-25 02:09:36 AM ]  File: Better.Call.Saul.S03E04.mkv
[ 2017-06-25 02:09:36 AM ]  RARBG found in container title (or filename)...
[ 2017-06-25 02:09:36 AM ]  Found 4 image/jpeg attachments, subs most likely not cleaned...
[ 2017-06-25 02:09:36 AM ]  ['C:\\Program Files\\MKVToolNix\\mkvextract.exe', 'tracks', 'S:\\TV\\Better Call Saul\\Season 03\\Better.Call.Saul.S03E04.mkv', u'2:S:\\TV\\Better Call Saul\\Season 03\\sub2.srt', u'3:S:\\TV\\Better Call Saul\\Season 03\\sub3.srt']
[ 2017-06-25 02:09:36 AM ]  Extracting 2 subtitle track(s)...
[ 2017-06-25 02:09:57 AM ]  Cleaning sub 2:S:\TV\Better Call Saul\Season 03\sub2.srt:
[ 2017-06-25 02:09:57 AM ]  Cleaning sub 3:S:\TV\Better Call Saul\Season 03\sub3.srt:
[ 2017-06-25 02:09:57 AM ]  Processing S:\TV\Better Call Saul\Season 03\Better.Call.Saul.S03E04.mkv ...
[ 2017-06-25 02:09:57 AM ]  ['C:\\Program Files\\MKVToolNix\\mkvmerge.exe', '--output', 'S:\\TV\\Better Call Saul\\Season 03\\output.mkv', '--no-subtitles', '--no-attachments', 'S:\\TV\\Better Call Saul\\Season 03\\Better.Call.Saul.S03E04.mkv', '--language', u'0:eng', 'S:\\TV\\Better Call Saul\\Season 03\\sub2.srt', '--language', u'0:eng', '--track-name', u'0:SDH', 'S:\\TV\\Better Call Saul\\Season 03\\sub3.srt']
[ 2017-06-25 02:10:27 AM ]  Remux of S:\TV\Better Call Saul\Season 03\Better.Call.Saul.S03E04.mkv successful.
[ 2017-06-25 02:10:27 AM ]  Removing: S:\TV\Better Call Saul\Season 03\sub2.srt
[ 2017-06-25 02:10:27 AM ]  Removing: S:\TV\Better Call Saul\Season 03\sub3.srt
[ 2017-06-25 02:10:27 AM ]  Preserving timestamp of S:\TV\Better Call Saul\Season 03\Better.Call.Saul.S03E04.mkv
[ 2017-06-25 02:10:28 AM ]  Renamed: S:\TV\Better Call Saul\Season 03\output.mkv to S:\TV\Better Call Saul\Season 03\Better.Call.Saul.S03E04.mkv
[ 2017-06-25 02:10:28 AM ]  --
[ 2017-06-25 02:10:28 AM ]  Finished processing.
```

# fix_rarbg
Clean up RARBG watermarks

## Watermarks

Sites sometimes add watermarks covers and advertisement in the subs.
While there are plenty of utilities out there to clean up subs there are not much for covers.

### Overview

Several years ago I made this quick script to clean things up.
It was was made back when python2 still preferred (which is why this does not gracefully handle unicode).

Requires MKVToolNix (v28+)
Install in default location or pass arguments to mkvmerge/mkvextract.


1) **Analyzing file/folder**

See if RARBG is found in container title or filename.
If there are jpeg attachments, assume file has not been sanitized.
This allows you to blindly run this on folders or downloads as a post-processing job.

2) **Subs**

  Look for SRT subs, extract.
  Exclude lines with RARBG in them.

3) **Remux**

  Drop attachments, remux with new subs.

4) **Cleanup**

  By default, the file timestamp is preserved from original file.


#### Notes
Looking at the .mkv you might see:
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

Identifying the attachments and dropping is trivial.
```
mkvpropedit file.mkv --delete-attachment mime-type:image/jpeg
```
> Updates file inline instantly.. doesnt remux file so original encoding info/date is still present.. does not reclaim space.

```
mkvmerge file.mkv --no-attachments -o output.mkv
```
> Takes a moment due to remux. Reclaims space and will have new encode date.

To cleanup the subs however takes a little more work as you ahve to extract, clean, then remux.

#### Sample
snippet of log file (file name truncated):
```
[ 2017-06-26 06:52:21 PM ]  Identifying video (1/8)
[ 2017-06-26 06:52:21 PM ]  File: Archer.2009.S08E01.mkv
[ 2017-06-26 06:52:21 PM ]  RARBG found in container title (or filename)...
[ 2017-06-26 06:52:21 PM ]  Found 4 image/jpeg attachments, subs most likely not cleaned...
[ 2017-06-26 06:52:21 PM ]  Extracting 2 subtitle track(s)...
[ 2017-06-26 06:52:30 PM ]  Cleaning 2:S:\TV\Archer (2009)\Season 08\sub2.srt
[ 2017-06-26 06:52:30 PM ]  Cleaning 3:S:\TV\Archer (2009)\Season 08\sub3.srt
[ 2017-06-26 06:52:30 PM ]  Processing S:\TV\Archer (2009)\Season 08\Archer.2009.S08E01.mkv ...
[ 2017-06-26 06:52:42 PM ]  Remux of S:\TV\Archer (2009)\Season 08\Archer.2009.S08E01.mkv successful.
[ 2017-06-26 06:52:43 PM ]  Preserving timestamp of S:\TV\Archer (2009)\Season 08\Archer.2009.S08E01.mkv
```

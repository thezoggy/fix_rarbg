#!/usr/bin/env python -OO

import os
import sys
import atexit
import subprocess
import json

from datetime import datetime
from argparse import ArgumentParser


# Location for mkvmerge + mkvextract binaries.
# The location always uses the / versus the \ as appropriate for some OSes.
MKVMERGE_BIN = 'C:/Program Files/MKVToolNix/mkvmerge.exe'
MKVEXTRACT_BIN = 'C:/Program Files/MKVToolNix/mkvextract.exe'

# Generate LOG file? Log file will be in the same directory as the script
LOG = True

# process current directory that the script is in, unless provided otherwise.
# if you are going to hardcode a path here, use / not \ for your separator (yes you windows peeps)
DIR = os.path.dirname(os.path.realpath(__file__))

# modify files or just do dry run so you can check logs to see if it will do what you want
DRY_RUN = True

# PRESERVE_TIMESTAMP keeps the timestamps of the old file if set. ** recommended
PRESERVE_TIMESTAMP = True

VERBOSE = False

for i in [
        'MKVMERGE_BIN',
        'MKVEXTRACT_BIN',
        'LOG',
        'DIR',
        'DRY_RUN',
        'PRESERVE_TIMESTAMP',
        'VERBOSE'
        ]:
    if i not in globals():
        raise RuntimeError('%s configuration variable is required.' % (i))


class Logger(object):
    _files = dict()

    @staticmethod
    def init(*args):
        for path in args:
            if path not in Logger._files:
                Logger._files[path] = open(path, 'w')
                Logger.write('Log file opened at', path)
                Logger.write('--')

    @staticmethod
    def write(*args, **kwargs):
        for k in kwargs:
            if k not in ['stderr', 'indent']:
                raise TypeError('write() got an unexpected keyword argument \'%s\'' % (k))

        ts = datetime.now().strftime('[ %Y-%m-%d %I:%M:%S %p ] ')
        msg = ' '.join(str(i) for i in args)

        # Build list of files to log to
        files = list()
        if 'stderr' in kwargs:
            files.append(sys.stderr)
        else:
            files.append(sys.stdout)
        files += Logger._files.values()

        for f in files:
            print >> f, ts,
            if 'indent' in kwargs:
                Logger._indent(kwargs['indent'], f)
            print >> f, msg

    @staticmethod
    def destroy():
        Logger.write('--')
        Logger.write('Finished processing.')
        for f in Logger._files.values():
            f.close()

    @staticmethod
    def _indent(x, content):
        for _i in range(x):
            print >> content, ' ',


atexit.register(Logger.destroy)

parser = ArgumentParser(description='Clean up RARBG subs and removes attachments from MKV files.')
group = parser.add_mutually_exclusive_group()
group.add_argument('-l', '--log', default=None, action='store_true', help='Create log file.')
group.add_argument('--no-log', default=None, action='store_false', dest='log', help='Do not create log file.')
parser.add_argument('-d', '--dir', default=DIR, help='Pass file or folder to process')
group = parser.add_mutually_exclusive_group()
group.add_argument('-t', '--test-run', default=None, action='store_true', help='Do not perform actions on files.')
group.add_argument('--no-test-run', default=None, action='store_false', dest='test_run', help='Perform actions on files.')
group = parser.add_mutually_exclusive_group()
group.add_argument('-p', '--preserve-timestamp', default=None, action='store_true', help='Use source timestamp for remux file.')
group.add_argument('--no-preserve-timestamp', default=None, action='store_false', dest='preserve_timestamp', help='Do not use source timestamp for remux file.')
parser.add_argument('-m', '--mkvmerge-bin', default=MKVMERGE_BIN, help='Path to mkvmerge binary.')
parser.add_argument('-e', '--mkvextract-bin', default=MKVEXTRACT_BIN, help='Path to mkvextract binary.')
parser.add_argument('-v', '--verbose', default=None, action='store_true', dest='verbose', help='Be verbose with output.')
args = parser.parse_args()


###################################################################################################
if sys.version_info[:2] < (2, 7) or sys.version_info[:2] >= (3, 0):
    print "Sorry, requires Python 2.7."
    sys.exit(1)

# Make sure UTF-8 is default 8bit encoding
if not hasattr(sys, "setdefaultencoding"):
    reload(sys)
try:
    sys.setdefaultencoding('utf-8')
except:
    print 'UTF-8 is not supported on this system... fix it!'
    sys.exit(1)

import locale
import __builtin__
try:
    locale.setlocale(locale.LC_ALL, "")
    __builtin__.__dict__['codepage'] = locale.getlocale()[1] or 'cp1252'
except:
    # Work-around for Python-ports with bad "locale" support
    __builtin__.__dict__['codepage'] = 'cp1252'
###################################################################################################


LOG = LOG if args.log is None else args.log
if LOG:
    LOG_DIR = os.path.dirname(os.path.realpath(__file__))
    LOG_FILE = datetime.now().strftime('log_%Y%m%d-%H%M%S.log')
    LOG_PATH = os.path.abspath(os.path.join(LOG_DIR, LOG_FILE))
    Logger.init(LOG_PATH)

Logger.write('Running', os.path.basename(__file__), 'with configuration:')

MKVMERGE_BIN = os.path.abspath(args.mkvmerge_bin)
Logger.write('MKVMERGE_BIN =', MKVMERGE_BIN)

MKVEXTRACT_BIN = os.path.abspath(args.mkvextract_bin)
Logger.write('MKVEXTRACT_BIN =', MKVEXTRACT_BIN)

DIR = os.path.abspath(args.dir)
Logger.write('DIR =', DIR)

DRY_RUN = DRY_RUN if args.test_run is None else args.test_run
Logger.write('DRY_RUN =', DRY_RUN)

PRESERVE_TIMESTAMP = PRESERVE_TIMESTAMP if args.preserve_timestamp is None else args.preserve_timestamp
Logger.write('PRESERVE_TIMESTAMP =', PRESERVE_TIMESTAMP)

VERBOSE = VERBOSE if args.verbose is None else args.verbose
Logger.write('VERBOSE =', VERBOSE)

Logger.write('--')
processList = list()
if os.path.isfile(DIR) is True:
    processList.append(DIR)
else:
    # Walk through the directory and sort by filename
    unsortedList = list()
    for dirpath, dirnames, filenames in os.walk(DIR):
        mkvFilenames = [filename for filename in filenames if filename.lower().endswith('.mkv')]
        mkvFilenames.sort()
        unsortedList.append((dirpath, mkvFilenames))

    # Now sort by Directory and append to processList
    unsortedList.sort(key=lambda dirTuple: dirTuple[0])
    for dirpath, filenames in unsortedList:
        for filename in filenames:
            processList.append(os.path.join(dirpath, filename))

totalMKVs = len(processList)
Logger.write('Analyzing %s videos' % totalMKVs)
counter = 0

for path in processList:
    counter += 1
    Logger.write('==========================================')

    basepath, basename = os.path.split(path)

    # identify file
    Logger.write('Identifying video (%s/%s)' % (counter, totalMKVs))
    Logger.write("File: %s" % (basename))

    cmd = [MKVMERGE_BIN, '--ui-language', 'en', '--identification-format', 'json', '--identify', path]

    if VERBOSE:
        Logger.write(cmd)

    try:
        result = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        Logger.write('Failed to identify', path, stderr=True)
        continue
    # import json output into data structure
    output = json.loads(result)

    # since we dont know if the filename is obfuscated at this point, use container title
    title = ''
    try:
        title = output['container']['properties']['title']
    except KeyError:
        # fallback to filename
        title = basename

    # only continue if we find RARBG
    if 'rarbg' in title.lower():
        Logger.write('RARBG found in container title (or filename)...')
    else:
        if VERBOSE:
            Logger.write('RARBG not found in title (or filename), skipping.')
        continue

    # look for image/jpeg attachments (rarbg logos)
    jpg_attachment = 0
    try:
        for attachment in output['attachments']:
            if attachment['content_type'] == "image/jpeg":
                jpg_attachment += 1
    except:
        pass

    # if there is attachments.. assume this script has not sanitized the files
    if jpg_attachment > 0:
        Logger.write('\033[91mFound %i image/jpeg attachments, subs most likely not cleaned...\033[00m' % jpg_attachment)
    else:
        if VERBOSE:
            Logger.write('No attachments found, subs most likely already cleaned.')
        continue

    # find subs
    subtitles = list()
    for line in output['tracks']:
        if line['type'] == "subtitles" and line['codec'] == "SubRip/SRT":
            # Logger.write(line, indent=1)
            subtitles.append(str(line['id']) + u':' + os.path.join(basepath, "sub" + str(line['id']) + ".srt"))

    if len(subtitles) > 0:
        cmd = [MKVEXTRACT_BIN, 'tracks', path]
        cmd.extend(subtitles)
    else:
        if VERBOSE:
            Logger.write('No SRT subs found to extract.. skipping.')
        continue

    if VERBOSE:
        Logger.write(cmd)

    if DRY_RUN is False:
        # extract subs
        Logger.write('Extracting %i subtitle track(s)...' % (len(subtitles)))
        try:
            result = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            Logger.write('Failed to extract tracks', path, stderr=True)
            continue

        # clean subs
        for entry in subtitles:
            Logger.write('Cleaning %s' % (entry))
            # remove the track id
            entry = entry.split(':', 1)[1]
            with open(entry, "r") as f:
                lines = (line.rstrip() for line in f)
                altered_lines = [' ' if "RARBG" in line else line for line in lines]
            with open(entry, "w") as f:
                f.write('\n'.join(altered_lines) + '\n')

    # generate output json
    cmd_output = list()
    cmd_output.extend(["--no-subtitles", "--no-attachments", path])
    for line in output['tracks']:
        if line['type'] == "subtitles" and line['codec'] == "SubRip/SRT":
            try:
                if line['properties']['language']:
                    cmd_output.extend(["--language", "0:" + line['properties']['language']])
            except KeyError:
                pass
            try:
                if line['properties']['track_name']:
                    cmd_output.extend(["--track-name", "0:" + line['properties']['track_name']])
            except KeyError:
                pass
            cmd_output.append(os.path.join(basepath, "sub" + str(line['id']) + ".srt"))

    target = os.path.join(basepath, "output.mkv")
    cmd = [MKVMERGE_BIN, "--output", target]
    cmd.extend(cmd_output)

    if VERBOSE:
        Logger.write(cmd)

    if DRY_RUN is False:
        Logger.write('Processing %s ...' % (path))
        try:
            result = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as e:
            Logger.write('Remux of', path, 'failed!', stderr=True)
            Logger.write(e.cmd, stderr=True)
            Logger.write(e.output, stderr=True)

            continue
        else:
            Logger.write('Remux of', path, 'successful.')
            # cleanup extracted subs
            for filename in subtitles:
                sfilename = filename.split(':', 1)[1]
                if VERBOSE:
                    Logger.write('Removing: %s' % (sfilename))
                os.unlink(sfilename)

    # Preserve timestamp
    if DRY_RUN is False:
        if PRESERVE_TIMESTAMP is True:
            Logger.write('Preserving timestamp of', path)
            if DRY_RUN is False:
                stat = os.stat(path)
                os.utime(target, (stat.st_atime, stat.st_mtime))

    # Replace original file
    if DRY_RUN is False:
        try:
            os.unlink(path)
        except:
            os.unlink(target)
            Logger.write('Renaming of', target, 'to', path, 'failed!', stderr=True)
        else:
            os.rename(target, path)
            if VERBOSE:
                Logger.write('Renamed: %s to %s' % (target, path))

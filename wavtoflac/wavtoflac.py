import os
import shutil
from enum import Enum

from mutagen.flac import FLAC
from pydub import AudioSegment
from termcolor import cprint

# Defaults
HOME = os.path.expanduser("~")
PATH_IN = os.path.join(HOME, "../../media/lmertens/MusicMorryII/Music")
PATH_OUT = os.path.join(HOME, "../../media/lmertens/SD_CARD/MUSIC")


class Format(Enum):
    WAV = '.wav'
    FLAC = '.flac'


class WAVToFlac:
    def __init__(self):
        self.failed = []

    def parse_dir_convert(self, path, ref_path, to_copy=None, b_initial=True):
        """

        :param path: the path to parse
        :param ref_path: this is the path you will first call the method will. After the initial call, the method
        will recursively traverse subpaths, and use this 'original' path to extract the names of the directories
        specific to the music being parsed. If this doesn't make any sense, read the code.
        :param to_copy: an optional set of file extensions that should be copied from PATH_IN to PATH_OUT.
        :param b_initial: boolean indicating that this call did not originate from within the method itself. Should
        not be specified by the user.
        :return:
        """
        if to_copy is None:
            to_copy = set()
        elif not isinstance(to_copy, set):
            raise ValueError(f"Argument 'to_copy' should be of type 'set', got '{to_copy.__class__.__name__}' instead.")

        # Reset container for failed files
        if b_initial:
            self.failed = []

        # Get file extension, if applicable (i.e., we're not dealing with a directory)
        ext = path.rsplit('.', 1)
        if len(ext) == 2:
            ext = ext[1]
        else:
            ext = ''

        for elem in os.listdir(path):
            full_path_in = os.path.join(path, elem)
            if os.path.isdir(full_path_in):
                self.parse_dir_convert(full_path_in, ref_path, b_initial=False)
            elif full_path_in.endswith(".wav"):
                full_dir_out = os.path.dirname(full_path_in).replace(PATH_IN, PATH_OUT)
                if not os.path.exists(full_dir_out):
                    os.makedirs(full_dir_out)
                full_path_out = os.path.join(full_dir_out, elem).replace('.wav', '.flac')
                if os.path.isfile(full_path_out):
                    continue

                tags = self._extract_tags(full_path_in, ref_path, audio_format=Format.WAV)

                print(f"Converting '{elem}' to\n\t[{full_path_out}]")

                # Convert to flac
                # ### PyDub
                try:
                    song = AudioSegment.from_wav(full_path_in)
                    song.export(full_path_out, format='flac', tags=tags)
                except Exception as e:
                    print(e.__class__.__name__)
                    print(e)
                    self.failed.append(full_path_in)

                # ### Python Audio Tools
                # audio_file = audiotools.open(full_path_in)
                # audio_file.convert(full_path_out, audiotools.FlacAudio)
            # Is this a file that should be copied?
            elif ext in to_copy:
                full_dir_out = os.path.dirname(full_path_in).replace(PATH_IN, PATH_OUT)
                if not os.path.exists(full_dir_out):
                    os.makedirs(full_dir_out)
                full_path_out = os.path.join(full_dir_out, elem)
                if os.path.isfile(full_path_out):
                    continue
                print(f"Copying [{full_path_in}] to\n\t[{full_path_out}]")
                shutil.copyfile(full_path_in, full_path_out)

        if b_initial:
            print()
            if not self.failed:
                print("All files converted successfully.")
            else:
                for e in self.failed:
                    print(f"Failed to process: [{e}]")

    def parse_dir_update_tags(self, path, ref_path, b_initial=True):
        # Reset container for failed files
        if path == ref_path:
            self.failed = []

        for elem in os.listdir(path):
            full_path_in = os.path.join(path, elem)
            if os.path.isdir(full_path_in):
                self.parse_dir_update_tags(full_path_in, ref_path, b_initial=False)
            elif full_path_in.endswith(".flac"):
                tags = self._extract_tags(full_path_in, ref_path)

                try:
                    song = FLAC(full_path_in)
                    song.clear()
                    song.update(tags)
                    song.save()
                except Exception as e:
                    print(e.__class__.__name__)
                    print(e)
                    self.failed.append(full_path_in)

        if b_initial:
            print()
            if not self.failed:
                print("All files converted successfully.")
            else:
                for e in self.failed:
                    print(f"Failed to process: [{e}]")

    @classmethod
    def _extract_tags(cls, path: str, ref_path: str, audio_format: Format = Format.FLAC):
        """
        Extract tags from path and filename

        Directories containing albums are expected to be in the following format:
        "Artist - Album/" or "Artist - (year) - Album/"
        Albums that span multible discs are supposed to be in the following format:
        "Artist - Album/Disc x/" or "Artist - (year) - Album/Disc x/",
        with a "disc x" directory fo each disc, where 'x' should be replaced by the index of the disc.

        Audiobook should follow the following format:
        "Author/Book/Disc x/

        :param path: the path to parse
        :param ref_path: the reference path (=root path of the collection)
        :param audio_format: file format
        :return:
        """
        tags = {}

        # Get total number of tracks for disc
        nb_tracks = len([x for x in os.listdir(os.path.dirname(path)) if x.endswith(audio_format.value)])
        tags['totaltracks'] = str(nb_tracks)

        elem = path[path.rfind('/')+1:]
        album_dir = os.path.dirname(path).replace(ref_path, '')[1:]  # Only the 'artist - album/disc' part
        len_dir = len(album_dir.split('/'))

        # Parse directory/ies
        if len_dir == 1:
            tags['totaldiscs'] = '1'
            dir_parts = [x.strip() for x in album_dir.split(' - ', 2)]

            tags['artist'] = dir_parts[0]
            if len(dir_parts) == 2:
                tags['album'] = dir_parts[1]
            elif len(dir_parts) == 3:
                tags['album'] = dir_parts[2]
                tags['date'] = dir_parts[1][1:-1]
            # else:
            #     raise ValueError(f"Don't know what to do here!\n{path}")
        elif len_dir == 2:
            # Get number of discs
            root_album_dir = path.rsplit('/', 2)[0]  # Full path to 'artist - album' part, without the 'disc' folder
            nb_discs = len([x for x in os.listdir(root_album_dir) if os.path.isdir(os.path.join(root_album_dir, x))])
            tags['totaldiscs'] = str(nb_discs)

            album_dir_parts = album_dir.split('/')
            root_dir, disc_dir = album_dir_parts[0], album_dir_parts[1]

            dir_parts = [x.strip() for x in root_dir.split(' - ', 2)]

            tags['artist'] = dir_parts[0]
            if len(dir_parts) == 2:
                tags['album'] = dir_parts[1]
            elif len(dir_parts) == 3:
                tags['album'] = dir_parts[2]
                tags['date'] = dir_parts[1][1:-1]

            disc_nr = cls._extract_discnr(disc_dir)
            if disc_nr:
                tags['discnumber'] = disc_nr

            # else:
            #     raise ValueError(f"DiscDir: Don't know what to do here!\n{path}\n{album_dir}\n{disc_dir}")
        # Audiobooks
        elif len_dir == 3:
            album_dir_parts = album_dir.split('/')
            author_dir, book_dir, disc_dir = album_dir_parts[0], album_dir_parts[1], album_dir_parts[2]

            # Get number of discs
            root_album_dir = path.rsplit('/', 2)[0]  # Full path to 'artist - album' part, without the 'disc' folder
            nb_discs = len([x for x in os.listdir(root_album_dir) if os.path.isdir(os.path.join(root_album_dir, x))])
            tags['totaldiscs'] = str(nb_discs)

            tags['author'] = author_dir
            tags['artist'] = author_dir
            tags['album'] = book_dir

            disc_nr = cls._extract_discnr(disc_dir)
            if disc_nr:
                tags['discnumber'] = disc_nr

        else:
            cprint(f"Don't know what to do here!\n{path}\n{album_dir}", color='cyan')

        # Strip extension and extract tags from filename
        elem = elem[:elem.rfind('.')]
        if len(elem) > 3 and elem[:2].isdecimal() and elem[2] == '-' or \
                len(elem) > 5 and elem[:2].isdecimal() and elem[3] == '-':
            song_parts = [x.strip() for x in elem.split('-', maxsplit=1)]
        else:
            song_parts = [x.strip() for x in elem.split(' ', maxsplit=1)]

        if len(song_parts) == 2:
            tags['tracknumber'] = song_parts[0]
            tags['title'] = song_parts[1]
        elif len(song_parts) == 1:
            tags['title'] = song_parts[0]
        else:
            raise ValueError(f"Don't know what to do with:\n\t[{song_parts}]")

        return tags

    @classmethod
    def _extract_discnr(cls, disc_dir: str):
        res = ''

        offset = 4
        disc_dir = disc_dir.lower()
        start_idx = disc_dir.find('disc')
        if start_idx == -1:
            start_idx = disc_dir.find('cd')
            offset = 2
        if start_idx == -1:
            return res

        for c in disc_dir[start_idx + offset:]:
            if c == ' ':
                continue
            elif c.isdigit():
                res += c
            else:
                break

        # if disc_dir.lower().startswith('disc'):
        #     disc_nr = disc_dir[4:].strip()
        #     if disc_nr.isdigit():
        #         res = disc_nr
        #
        # elif disc_dir.lower().startswith('cd'):
        #     disc_nr = disc_dir[2:].strip()
        #     if disc_nr.isdigit():
        #         res = disc_nr

        return res


if __name__ == '__main__':
    w2f = WAVToFlac()
    # w2f.parse_dir_convert(PATH_IN, PATH_IN, to_copy={'mp3', 'flac'})
    w2f.parse_dir_update_tags(PATH_OUT, ref_path=PATH_OUT)

import os
import shutil
from termcolor import cprint

from mutagen.flac import FLAC
from pydub import AudioSegment

# Defaults
HOME = os.path.expanduser("~")
PATH_IN = os.path.join(HOME, "../../media/lmertens/MusicMorryII/Music")
PATH_OUT = os.path.join(HOME, "../../media/lmertens/SD_CARD/MUSIC")


# class Format(Enum):
#     WAV = '.wav'
#     FLAC = '.flac'


class WAVToFlac:
    def __init__(self):
        self.failed = []

    def parse_dir_convert(self, path, ref_path, b_initial=True):
        """

        :param path: the path to parse
        :param ref_path: this is the path you will first call the method will. After the initial call, the method
        will recursively traverse subpaths, and use this 'original' path to extract the names of the directories
        specific to the music being parsed. If this doesn't make any sense, read the code.
        :return:
        """
        # Reset container for failed files
        if path == ref_path:
            self.failed = []

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

                tags = self._extract_tags(full_path_in, ref_path)

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
            elif full_path_in.endswith(".flac"):
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

    def _extract_tags(self, path: str, ref_path: str):
        """
        Extract tags from path and filename

        Directories containing albums are expected to be in the following format:
        "artist - album" or "artist - (year) - album"

        :param path: the path to parse
        :param ref_path: the reference path (=root path of the collection)
        :param format: file format
        :return:
        """
        elem = path[path.rfind('/')+1:]
        album_dir = os.path.dirname(path).replace(ref_path, '')[1:]
        len_dir = len(album_dir.split('/'))

        tags = {}
        if len_dir == 1:
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
            album_dir_parts = album_dir.split('/')
            root_dir, disc_dir = album_dir_parts[0], album_dir_parts[1]

            dir_parts = [x.strip() for x in root_dir.split(' - ', 2)]

            tags['artist'] = dir_parts[0]
            if len(dir_parts) == 2:
                tags['album'] = dir_parts[1]
            elif len(dir_parts) == 3:
                tags['album'] = dir_parts[2]
                tags['date'] = dir_parts[1][1:-1]

            if disc_dir.lower().startswith('disc'):
                disc_nr = disc_dir[4:].strip()
                tags['discnumber'] = disc_nr
                print(f"Path: {path}\n\tDiscnumber: {disc_nr}")

            elif disc_dir.lower().startswith('cd'):
                disc_nr = disc_dir[2:].strip()
                tags['discnumber'] = disc_nr
                print(f"Path: {path}\n\tDiscnumber: {disc_nr}")

            # else:
            #     raise ValueError(f"DiscDir: Don't know what to do here!\n{path}\n{album_dir}\n{disc_dir}")

        else:
            cprint(f"Don't know what to do here!\n{path}\n{album_dir}", color='cyan')

        # Strip extension
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


if __name__ == '__main__':
    w2f = WAVToFlac()
    # w2f.parse_dir_convert(PATH_IN, PATH_IN)
    w2f.parse_dir_update_tags(PATH_OUT, ref_path=PATH_OUT)

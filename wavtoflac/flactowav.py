"""
Convert files in flac to wav, following same directory structure.

.. codeauthor:: Laurent Mertens <laurent.mertens@kuleuven.be>
"""
import os
import shutil
from enum import Enum

from mutagen.flac import FLAC
from pydub import AudioSegment
from termcolor import cprint

# Defaults
HOME = os.path.expanduser("~")
PATH_IN = os.path.join(HOME, "../../media/lmertens/SD_CARD/MUSIC")
PATH_OUT = os.path.join(HOME, "../../media/lmertens/MusicMorryII/Music")


class Format(Enum):
    FLAC = '.flac'
    MP3 = '.mp3'
    WAV = '.wav'


class FlacToWAV:
    def __init__(self):
        self.failed = []

    def parse_dir_convert(self, path, ref_path, to_copy=None, b_initial=True):
        """

        :param path: the path to parse
        :param ref_path: this is the path you will first call the method with. After the initial call, the method
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

        for elem in os.listdir(path):
            full_path_in = os.path.join(path, elem)
            # Get file extension, if applicable (i.e., we're not dealing with a directory)
            ext = elem.rsplit('.', 1)
            if len(ext) == 2:
                ext = ext[1]
            else:
                ext = ''

            if os.path.isdir(full_path_in):
                self.parse_dir_convert(full_path_in, ref_path, to_copy, b_initial=False)
            elif ext == "flac":
                full_dir_out = os.path.dirname(full_path_in).replace(PATH_IN, PATH_OUT)
                if not os.path.exists(full_dir_out):
                    os.makedirs(full_dir_out)
                full_path_out = os.path.join(full_dir_out, elem).replace('.flac', '.wav')
                if os.path.isfile(full_path_out):
                    continue

                print(f"Converting '{elem}' to\n\t[{full_path_out}]")

                # Convert to WAV
                # ### PyDub
                try:
                    song = AudioSegment.from_file(full_path_in, format='flac')
                    song.export(full_path_out, format='wav')
                except Exception as e:
                    print(e.__class__.__name__)
                    print(e)
                    self.failed.append(full_path_in)

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


if __name__ == '__main__':
    f2w = FlacToWAV()
    f2w.parse_dir_convert(PATH_IN, PATH_IN, to_copy={'mp3', 'wav', 'jpg', 'jpeg', 'png'})
    # w2f.parse_dir_update_tags(PATH_OUT, ref_path=PATH_OUT)

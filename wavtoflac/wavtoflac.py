import math
import os
import shutil
from enum import Enum

from PIL import Image
from mutagen import id3
from ffmpeg import FFmpeg
from mutagen.flac import FLAC, Picture
from pydub import AudioSegment
from termcolor import cprint

# Defaults
HOME = os.path.expanduser("~")
PATH_IN = os.path.join(HOME, "../../media/lmertens/MusicMorryIII/Music")
# PATH_OUT = os.path.join(HOME, "../../media/lmertens/SD_CARD/MUSIC")
PATH_OUT = os.path.join(HOME, "../../media/lmertens/3039-3962/MUSIC")

MODE_TO_BPP = {"1": 1, "L": 8, "P": 8, "RGB": 24, "RGBA": 32, "CMYK": 32, "YCbCr": 24, "LAB": 24,
               "HSV": 24, "I": 32, "F": 32}

class Format(Enum):
    AAC = '.aac'
    FLAC = '.flac'
    MP3 = '.mp3'
    MPGA = '.mpga'
    WAV = '.wav'


class WAVToFlac:
    def __init__(self):
        self.failed = []
        # ref_path: this is the path you will first call the method with. After the initial call, the method
        # will recursively traverse subpaths, and use this 'original' path to extract the names of the directories
        # specific to the music being parsed. If this doesn't make any sense, read the code.
        self.ref_path = None
        self.b_add_cover = False

        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("To expand code to allow loading folder pictures, check comments in code.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # Taken from: https://mutagen.readthedocs.io/en/latest/api/flac.html#mutagen.flac.Picture
        # First, create a Picture object containing the appropriate image,
        # then, add this image to the FLAC object
        # pic = Picture()
        #
        # with open("Folder.jpg", "rb") as f:
        #     pic.data = f.read()
        #
        # pic.type = id3.PictureType.COVER_FRONT
        # pic.mime = u"image/jpeg"
        # pic.width = 500
        # pic.height = 500
        # pic.depth = 16 # color depth
        #
        #  flac_object.add_picture(picture)

    def check_dirs_out_to_in(self, path_in, path_out, b_delete=False):
        """
        Check which directories present on target device or path (path_out) are NOT present on source device or path (path_in).

        :param path_in: the path to parse.
        :param path_out: the output path in which the folder structure found within path_in will be mirrored.
        :param b_delete: delete path on target device if it does not exist on source device.
        :return:
        """
        for elem in sorted(os.listdir(path_out)):
            full_path_target = os.path.join(path_out, elem)
            if os.path.isdir(full_path_target):
                full_path_source = os.path.join(path_in, elem)
                if not os.path.exists(full_path_source):
                    print(f"Unmatched target path: {full_path_target}")
                    # print(f"\tFull path: {full_path_target}")
                    if b_delete:
                        shutil.rmtree(full_path_target)
                        print("\tPath deleted from target device.")
                else:
                    self.check_dirs_out_to_in(path_in=full_path_source, path_out=full_path_target, b_delete=b_delete)

    def parse_dir_convert(self, path_in, path_out, b_add_cover=False, to_copy=None, _b_initial=True):
        """
        Parse a directory to convert the WAV files to FLAC.

        :param path_in: the path to parse
        :param path_out: the output path in which the folder structure found within path_in will be mirrored.
        :param b_add_cover: try to add cover to converted FLAC files
        :param to_copy: an optional set of file extensions that should be copied from PATH_IN to PATH_OUT.
        :param _b_initial: boolean indicating that this call did not originate from within the method itself. Should
        not be specified by the user.
        :return:
        """
        if to_copy is None:
            to_copy = set()
        elif not isinstance(to_copy, set):
            raise ValueError(f"Argument 'to_copy' should be of type 'set', got '{to_copy.__class__.__name__}' instead.")

        # Reset container for failed files
        if _b_initial:
            self.failed = []
            self.ref_path = path_in
            self.b_add_cover = b_add_cover

        # First, check directory for presence of image file

        for elem in os.listdir(path_in):
            full_path_in = os.path.join(path_in, elem)
            # Get file extension, if applicable (i.e., we're not dealing with a directory)
            ext = elem.rsplit('.', 1)
            if len(ext) == 2:
                ext = ext[1].lower()
            else:
                ext = ''

            # If the element is a directory, recursively parse it
            if os.path.isdir(full_path_in):
                self.parse_dir_convert(full_path_in, path_out, to_copy=to_copy, _b_initial=False)
            elif ext == "wav":
                full_dir_out = os.path.dirname(full_path_in).replace(self.ref_path, path_out)
                if not os.path.exists(full_dir_out):
                    os.makedirs(full_dir_out)
                # Don't do ".replace('.wav', '.flac'), because that way you miss the cases
                # where the original file has '.WAV' in uppercase.
                full_path_out = os.path.join(full_dir_out, elem)[:-4] + '.flac'
                # File already exists? Then skip.
                if os.path.isfile(full_path_out):
                    continue

                tags, cover_pic = self._extract_tags(full_path_in, audio_format=Format.WAV)

                print(f"Converting '{elem}' to\n\t[{full_path_out}]")

                # Convert to flac
                # ### PyDub
                try:
                    song = AudioSegment.from_wav(full_path_in)

                    song.export(full_path_out, format='flac', tags=tags)
                    # Add cover image
                    if cover_pic is not None:
                        # Using FLAC library doesn't make the image show up on Sony Walkman device
                        # song = FLAC(full_path_out)
                        # song.add_picture(cover_pic)
                        # song.save()

                        # ffmpeg device to use
                        # ffmpeg -i song.flac -i image.jpg -map_metadata 0 -map 0 -map 1 -acodec copy -disposition:v attached_pic song_with_cover.flac
                        temp_file = full_path_out[:-5] + '_temp.flac'
                        ffmpeg = (
                            FFmpeg()
                            .input(full_path_out)
                            .input(cover_pic)
                            .output(temp_file,
                                {'map_metadata': 0,
                                 'acodec': 'copy',
                                 'disposition:v': 'attached_pic'}
                            )
                        )

                        # For debugging purposes
                        # @ffmpeg.on("start")
                        # def on_start(arguments: list[str]):
                        #     print("arguments:", arguments)
                        #
                        # @ffmpeg.on("stderr")
                        # def on_stderr(line):
                        #     print("stderr:", line)
                        #
                        # @ffmpeg.on("progress")
                        # def on_progress(progress):
                        #     print(progress)
                        #
                        # @ffmpeg.on("completed")
                        # def on_completed():
                        #     print("completed")
                        #
                        # @ffmpeg.on("terminated")
                        # def on_terminated():
                        #     print("terminated")

                        ffmpeg.execute()

                        os.remove(full_path_out)
                        os.rename(temp_file, full_path_out)

                        print(f"Attempted to add cover from image [{cover_pic}]...")

                except Exception as e:
                    print(e.__class__.__name__)
                    print(e)
                    self.failed.append(full_path_in)

                # ### Python Audio Tools
                # audio_file = audiotools.open(full_path_in)
                # audio_file.convert(full_path_out, audiotools.FlacAudio)

            elif ext == "mpga":
                full_dir_out = os.path.dirname(full_path_in).replace(self.ref_path, path_out)
                if not os.path.exists(full_dir_out):
                    os.makedirs(full_dir_out)
                # Don't do ".replace('.wav', '.flac'), because that way you miss the cases
                # where the original file has '.WAV' in uppercase.
                full_path_out = os.path.join(full_dir_out, elem)[:-4] + '.flac'
                # File already exists? Then skip.
                if os.path.isfile(full_path_out):
                    continue

                tags, cover_pic = self._extract_tags(full_path_in, audio_format=Format.MPGA)

                print(f"Converting '{elem}' to\n\t[{full_path_out}]")

                # Convert to flac
                # ### PyDub
                try:
                    song = AudioSegment.from_wav(full_path_in)

                    song.export(full_path_out, format='flac', tags=tags)
                    # Add cover image
                    if cover_pic is not None:
                        song = FLAC(full_path_out)
                        song.add_picture(cover_pic)
                        song.save()

                except Exception as e:
                    print(e.__class__.__name__)
                    print(e)
                    self.failed.append(full_path_in)

            # Is this a file that should be copied?
            elif ext in to_copy:
                full_dir_out = os.path.dirname(full_path_in).replace(self.ref_path, path_out)
                if not os.path.exists(full_dir_out):
                    os.makedirs(full_dir_out)
                full_path_out = os.path.join(full_dir_out, elem)
                if os.path.isfile(full_path_out):
                    continue
                print(f"Copying [{full_path_in}] to\n\t[{full_path_out}]")
                shutil.copyfile(full_path_in, full_path_out)

        if _b_initial:
            print()
            if not self.failed:
                print("All files converted successfully.")
            else:
                for e in self.failed:
                    print(f"Failed to process: [{e}]")

    def _parse_dir_update_tags(self, path, _b_initial=True):
        # Reset container for failed files
        if path == self.ref_path:
            self.failed = []

        for elem in os.listdir(path):
            full_path_in = os.path.join(path, elem)
            if os.path.isdir(full_path_in):
                self._parse_dir_update_tags(full_path_in, _b_initial=False)
            elif full_path_in.endswith(".flac"):
                tags, cover_pic = self._extract_tags(full_path_in, audio_format=Format.FLAC)

                try:
                    song = FLAC(full_path_in)
                    song.clear()
                    song.update(tags)
                    song.save()
                except Exception as e:
                    print(e.__class__.__name__)
                    print(e)
                    self.failed.append(full_path_in)

        if _b_initial:
            print()
            if not self.failed:
                print("All files converted successfully.")
            else:
                for e in self.failed:
                    print(f"Failed to process: [{e}]")

    def _extract_tags(self, path: str, audio_format: Format = Format.FLAC):
        """
        Extract tags from path and filename

        Directories containing albums are expected to be in the following format:
        "Artist - Album/" or "Artist - (year) - Album/"
        Albums that span multible discs are supposed to be in the following format:
        "Artist - Album/Disc x/" or "Artist - (year) - Album/Disc x/",
        with a "disc x" directory for each disc, where 'x' should be replaced by the index of the disc.

        Audiobook should follow the following format:
        "Author/Book/Disc x/

        :param path: the path to parse
        :param audio_format: file format
        :return: tags, cover_pic
        """
        tags = {}

        # Get directory for song
        dir_path = os.path.dirname(path)

        # Check directory for presence of jpg image, that we will assume represents the album cover.
        cover_pic = None
        if self.b_add_cover:
            cover_pic = self._look_for_cover(dir_path)
            if cover_pic is not None:
                cover_pic = os.path.join(dir_path, cover_pic)

            #     path_cover = os.path.join(dir_path, img_cover)
            #     path_cover_temp = os.path.splitext(path_cover)[0] + '_TEMP.jpg'
                with open(cover_pic, 'rb') as f:
                    img_pic = Image.open(f).convert('RGB')
                    if img_pic.height > 500:
                        conv = 500 / img_pic.height
                        new_width = round(img_pic.width*conv)
                        im_new = img_pic.resize((new_width, 500))
                        _main, _ext = os.path.splitext(cover_pic)
                        if not _ext.lower() in ('.jpg', '.jpeg'):
                            cover_pic = _main + '.jpg'
                        im_new.save(cover_pic, quality=95)
                        print(f"Resized cover image to {new_width}px x 500px.")

            #
            #     cover_pic = Picture()
            #     with open(path_cover_temp, 'rb') as f:
            #         img_pic = Image.open(f).convert('RGB')
            #         img_format = img_pic.format
            #         img_data = f.read()
            #
            #     cover_pic.data = img_data
            #     cover_pic.type = id3.PictureType.COVER_FRONT
            #     cover_pic.mime = f"image/{img_format}"
            #     cover_pic.width = 0  # auto-detect
            #     cover_pic.height = 0  # auto-detect
            #     cover_pic.depth = 0  # auto-detect
            #
            #     os.remove(path_cover_temp)
            #     print(f"Attempted to add cover from image [{path_cover}], mime type: [image/{img_format}]")

        # Get total number of tracks for disc
        nb_tracks = len([x for x in os.listdir(os.path.dirname(path)) if x.endswith(audio_format.value)])
        tags['totaltracks'] = str(nb_tracks)

        elem = path[path.rfind('/')+1:]
        album_dir = os.path.dirname(path).replace(self.ref_path, '')[1:]  # Only the 'artist - album/disc' part
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
            root_album_dir = path.rsplit('/', 2)[0]  # Full path to 'artist - album' part
            album_dir_parts = album_dir.split('/')
            root_dir, disc_dir = album_dir_parts[0], album_dir_parts[1]
            # Get number of discs/collections
            nb_discs = len([x for x in os.listdir(root_album_dir) if os.path.isdir(os.path.join(root_album_dir, x))])
            tags['totaldiscs'] = str(nb_discs)

            dir_parts = [x.strip() for x in root_dir.split(' - ', 2)]

            # Situation of one album composed of multiple discs, with folders ending with "Disc X" or "CD X"
            if "disc " in disc_dir.lower() or "cd " in disc_dir.lower() or "part " in disc_dir.lower():
                tags['artist'] = dir_parts[0]
                if len(dir_parts) == 2:
                    tags['album'] = dir_parts[1]
                elif len(dir_parts) == 3:
                    tags['album'] = dir_parts[2]
                    tags['date'] = dir_parts[1][1:-1]

                disc_nr = self._extract_discnr(disc_dir)
                if disc_nr:
                    tags['discnumber'] = disc_nr

            # Situation of one album composed of multiple discs, with each subfolder not ending with "Disc"/"CD"
            else:
                tags['artist'] = dir_parts[0]
                if len(dir_parts) == 2:
                    tags['album'] = f'{dir_parts[1]} - {disc_dir}'
                elif len(dir_parts) == 3:
                    tags['album'] = f'{dir_parts[2]} - {disc_dir}'
                    tags['date'] = dir_parts[1][1:-1]

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

            disc_nr = self._extract_discnr(disc_dir)
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

        return tags, cover_pic

    def _look_for_cover(self, dir_path):
        imgs = []
        for f in os.listdir(dir_path):
            if f.lower().endswith('.jpg') or f.lower().endswith('.png'):
                imgs.append(f)

        min_file = None  # In case of multiple jpg files, select the smallest one
        if len(imgs) == 1:
            min_file = imgs[0]
        elif imgs:
            min_idx, min_size = 0, math.inf
            for idx_f, f in enumerate(imgs):
                full_path = os.path.join(dir_path, f)
                if os.path.getsize(full_path) < min_size:
                    min_size = os.path.getsize(full_path)
                    min_idx = idx_f
            min_file = imgs[min_idx]

        return min_file

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
    w2f.check_dirs_out_to_in(path_out=PATH_OUT, path_in=PATH_IN, b_delete=False)
    w2f.parse_dir_convert(path_in=PATH_IN, path_out=PATH_OUT, b_add_cover=True,
                          to_copy={'mp3', 'flac', 'm4a', 'dsf', 'jpg', 'jpeg', 'png', 'aac', 'pdf'})

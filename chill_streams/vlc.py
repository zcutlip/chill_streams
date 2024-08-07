import glob
import os
import platform
import time
from pathlib import Path
from typing import List, Optional, Tuple

from . import logging
from .cmd import CMD
from .station_list import StationEntry


class VLCException(Exception):
    pass


class VLCLocator(CMD):
    VLC_PATH_ENV_VAR = "VLC_PATH"
    CMD_NAME = "which"
    ARGS = ["vlc"]

    def __init__(self):
        super().__init__(self.ARGS)
        self._location = self._locate()

    def _fix_exe_case(self, location):
        """
        Case insensitive filesystems will allow is to execute VLC or vlc,
        but things that match on process name, like AirFoil, look for the actual
        process name
        """
        if not location:
            raise Exception(f"no location: {location}")
        exe_upper = os.path.basename(location).upper()
        exe_lower = exe_upper.lower()
        dirname = os.path.dirname(location)
        dirglob = os.path.join(dirname, "*")
        items = glob.glob(dirglob)

        if location not in items:
            # No idea what we started with, so lets just reset to lower case
            location = os.path.join(dirname, exe_lower)

        if location not in items:
            # haven't found it yet, so lets try upper cse
            location = os.path.join(dirname, exe_upper)

        if location not in items:
            # nothing worked, so something has gone wrong, set to None
            location = None
        return location

    def _locate(self) -> str:
        loc = os.environ.get(self.VLC_PATH_ENV_VAR)
        if loc:
            if not os.path.exists(loc):
                loc = None
            else:
                loc = self._fix_exe_case(loc)
        if not loc:
            ret: int
            out_bytes, ret = self.run(capture_out=True, capture_err=True)
            out = out_bytes.decode("utf-8")
            out = out.rstrip()
            if ret == 0:
                loc = out
                loc = self._fix_exe_case(loc)
        if not loc:
            raise VLCException("Can't locate VLC")
        return loc

    @property
    def location(self):
        return self._location


class VLC(CMD):
    CMD_NAME = "vlc"
    PAUSE_SECS = 2.0

    def __init__(self, entry: StationEntry, ncurses: bool = True, vlc_path: Optional[str] = None, extra_args: List[str] = []):
        logger = logging.get_logger(__name__)
        self.entry = entry
        args = [entry.url]
        if entry.is_video:
            ncurses = False
        if ncurses:
            args.extend(["--intf", "ncurses"])
        else:
            args.extend(["--no-video-title-show", "--meta-title", entry.name])
        super().__init__(args, logger=logger)

        if not vlc_path:
            self._location = self._find_vlc()
        else:
            self._location = vlc_path

        self.argv[0] = self._location

    @property
    def location(self):
        return self._location

    def run(self) -> Tuple[bytes, int]:
        self._display_and_pause(self.PAUSE_SECS)
        run_tuple = super().run()
        self._check_iterm(run_tuple[1])
        return run_tuple

    def _display_and_pause(self, sec):
        print("")
        print("")
        print(f"Playing: {self.entry.ansi_colorized()}")
        print("")
        print("")
        time.sleep(sec)

    def _check_iterm(self, ret: int):
        terminfo_x_path = Path("~/.terminfo/x").expanduser()
        terminfo_s_path = Path("~/.terminfo/s").expanduser()

        if ret != 0 and "arm64" == platform.machine() and "Darwin" == platform.system():
            if not terminfo_x_path.exists() or not terminfo_s_path.exists():
                err_str = """
                It appears you're using arm64 macOS, where VLC has a bug. You may need to run:
                $ mkdir ~/.terminfo
                $ # for TERM=xterm-256color:
                $ ln -s /usr/share/terminfo/78 ~/.terminfo/x
                $ # for TERM=screen-256color:
                $ ln -s /usr/share/terminfo/73 ~/.terminfo/s
                """
                self.logger.error(f"{err_str}")

    def _find_vlc(self):
        locator = VLCLocator()
        loc = locator.location
        return loc

import os
import shutil

import audeer


def test_symlinks(tmpdir):
    program = 'ffmpeg'
    path = audeer.mkdir(os.path.join(tmpdir, 'bin'))
    command = shutil.which(program)
    assert os.path.exists(command)
    os.symlink(command, os.path.join(path, program))
    assert os.path.exists(os.path.join(path, program))

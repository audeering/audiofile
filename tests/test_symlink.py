import os
import shutil

import audeer


def test_symlinks(tmpdir):
    program = 'ffmpeg'
    path = audeer.mkdir(os.path.join(tmpdir, 'bin'))
    command = shutil.which(program)
    assert os.path.exists(command)
    local_command = os.path.join(path, program)
    os.symlink(command, local_command)
    assert os.path.exists(local_command)
    os.environ['PATH'] = path
    assert shutil.which(program) == local_command
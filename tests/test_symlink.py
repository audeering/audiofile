import os
import platform
import shutil

import audeer


def test_symlinks(tmpdir):
    program = 'ffmpeg'
    path = audeer.mkdir(os.path.join(tmpdir, 'bin'))
    command = shutil.which(program)
    if platform.system() == 'Windows':
        command += '.exe'
    assert os.path.exists(command)
    local_command = os.path.join(path, program)
    os.symlink(command, local_command)
    # shutil.copyfile(command, local_command)
    assert os.path.exists(local_command)
    print(os.environ['PATH'])
    os.environ['PATH'] = path
    print(os.environ['PATH'])
    assert shutil.which(program) == local_command

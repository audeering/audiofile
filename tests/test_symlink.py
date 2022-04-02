import os
import platform
import shutil

import pytest

import audeer


@pytest.fixture(scope='function')
def restore_system_path():
    """Fixture to hide system path in test."""
    current_path = os.environ['PATH']

    yield

    os.environ['PATH'] = current_path


@pytest.mark.parametrize(
    'program',
    [
        'ffmpeg',
        'mediainfo',
    ],
)
def test_symlinks(tmpdir, restore_system_path, program):
    path = audeer.mkdir(os.path.join(tmpdir, 'bin'))
    command = shutil.which(program)
    assert os.path.exists(command)
    local_command = os.path.join(path, program)
    if platform.system() == 'Windows':
        local_command += '.EXE'
    os.symlink(command, local_command)
    assert os.path.exists(local_command)
    os.environ['PATH'] = path
    assert shutil.which(program) == local_command

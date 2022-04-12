import contextlib
import logging


"""Import sox without warnings.

We can import sox,
even if its binaries are missing.
As this is valid behavior in audiofile,
we surpress all related output warnings
during import.

"""
with contextlib.redirect_stderr(None):
    import sox
logging.getLogger('sox').setLevel(logging.CRITICAL)

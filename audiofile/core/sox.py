import logging

import sox


# Disable warning outputs of sox as we use it with try
logging.getLogger('sox').setLevel(logging.CRITICAL)


SOX_ERRORS = (
    sox.core.SoxError,
    sox.core.SoxiError,
    FileNotFoundError,  # sox binary missing
)

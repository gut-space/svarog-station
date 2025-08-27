from contextlib import suppress
from datetime import timedelta
import os.path
import logging

import sh

from recipes.helpers import set_sh_defaults


@set_sh_defaults
def execute(working_dir: str, frequency: str, duration: timedelta, metadata, sh=sh):

    print("Executing satdump recipe, parameters:")
    print(f"  working_dir: {working_dir}")
    print(f"  frequency: {frequency}")
    print(f"  duration: {duration}")
    print(f"  metadata: {metadata.getAll()}")

    raw_path = os.path.join(working_dir, "signal.raw")

    cmd = "./satdump record thoutput --samplerate 3e6 --frequency 137e6 --baseband_format cf32 --source airspy --timeout 10"

    logging.critical(f"Satdump recipe not implemented yet.")

    # TODO: perform the actual recording here

    return [
        ("RAW", raw_path)
    ]

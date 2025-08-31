from datetime import timedelta
import logging
import os.path


from recipes.helpers import set_sh_defaults


@set_sh_defaults
def execute(working_dir: str, frequency: str, duration: timedelta, metadata, custom_command=None, sh=None):

    print("Executing satdump recipe, parameters:")
    print(f"  working_dir: {working_dir}")
    print(f"  frequency: {frequency}")
    print(f"  duration: {duration}")
    print(f"  metadata: {metadata.getAll()}")
    if custom_command:
        print(f"  custom_command: {custom_command}")

    raw_path = os.path.join(working_dir, "signal.raw")

    # Use custom command if provided, otherwise use default
    if custom_command:
        cmd = custom_command
    else:
        cmd = "./satdump record thoutput --samplerate 3e6 --frequency 137e6 --baseband_format cf32 --source airspy --timeout 10"

    print(f"Executing command: {cmd}")

    # TODO: perform the actual recording here using the custom command
    # For now, just log that we would execute the command
    logging.info(f"Would execute: {cmd}")
    logging.critical(f"Satdump recipe not implemented yet.")

    return [
        ("RAW", raw_path)
    ]

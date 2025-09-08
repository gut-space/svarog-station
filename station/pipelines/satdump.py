from datetime import timedelta
from contextlib import suppress
import logging
import os.path
import signal
import time
import sh


from pipelines.helpers import set_sh_defaults

def toname(sat_name):
    return sat_name.replace(" ", "-").replace("_", "-").lower()

@set_sh_defaults
def execute(working_dir: str, frequency: str, duration: timedelta, metadata, custom_command=None, sh=None):


    sat_name = toname(metadata.get('satellite'))

    print("Executing satdump recipe, parameters:")
    print(f"  working_dir: {working_dir}")
    print(f"  frequency: {frequency}")
    print(f"  duration: {duration}")
    print(f"  metadata: {metadata.getAll()}")
    print(f"  sat name: {sat_name}")
    if custom_command:
        print(f"  custom_command: {custom_command}")

    raw_path = os.path.join(working_dir, sat_name + ".raw")
    log_path = os.path.join(working_dir, sat_name + "-satdump.log")

    sdr_device = "airspy"
    gain = 21

    # Use custom command if provided, otherwise use default
    if custom_command:
        cmd = custom_command
    else:

        common_params = f"--samplerate 3e6 --frequency {frequency} --general_gain {gain} --baseband_format cf32 --source {sdr_device} --timeout {int(duration.total_seconds())}"

        match sat_name:
            case "noaa-15" | "noaa-18" | "noaa-19":
                cmd = f"satdump live noaa_apt {working_dir} {common_params}"
            case "meteor-m2-3" | "meteor-m2-4":
                cmd = f"satdump live meteor_m2-x_lrpt {working_dir} {common_params}"
            case _:
                cmd = f"satdump record {raw_path} {common_params}"

    cmd_bin = cmd.split()[0]
    cmd_args = cmd.split()[1:]

    logging.info(f"Executing command: {cmd_bin} {cmd_args}")

    satdump_proc = sh.satdump( *cmd_args,
        _err=log_path
    )
    print(f"satdump_proc.type(): {type(satdump_proc)}")
    print(f"satdump_proc: {satdump_proc}")
    try:
        satdump_proc.wait(duration.total_seconds()+15)
    except sh.TimeoutException:

        logging.info(f"Satdump process timed out after {duration.total_seconds()}+15 seconds")

    return [
        ("RAW", raw_path)
    ]

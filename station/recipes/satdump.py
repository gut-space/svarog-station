from datetime import timedelta
from contextlib import suppress
import logging
import os.path
import signal
import sh


from recipes.helpers import set_sh_defaults

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

    # Use custom command if provided, otherwise use default
    if custom_command:
        cmd = custom_command
    else:
        match sat_name:
            case "noaa-15" | "noaa-18" | "noaa-19":
                cmd = f"satdump live noaa_apt {working_dir} --samplerate 3e6 --frequency {frequency} --baseband_format cf32 " + \
                      f"--source {sdr_device} --timeout {int(duration.total_seconds())}"
            case "meteor-m2-3" | "meteor-m2-4":
                cmd = f"satdump live meteor_m2_lrpt {working_dir} --samplerate 3e6 --frequency {frequency} --baseband_format cf32 " + \
                      f"--source {sdr_device} --timeout {int(duration.total_seconds())}"
            case _:
                cmd = f"satdump record {raw_path} --samplerate 3e6 --frequency {frequency} --baseband_format cf32 " + \
                    f"--source {sdr_device} --timeout {int(duration.total_seconds())}"

    cmd_bin = cmd.split()[0]
    cmd_args = cmd.split()[1:]

    logging.info(f"Executing command: {cmd_bin} {cmd_args}")

    with suppress(sh.TimeoutException):
        satdump_proc = sh.satdump( *cmd_args,
            _timeout=duration.total_seconds(),
            _timeout_signal=signal.SIGHUP,

            # rtl_fm and rx_fm both print messages on stderr
            _err=log_path
        )
        satdump_proc.send_signal(signal.SIGKILL)

    return [
        ("RAW", raw_path)
    ]

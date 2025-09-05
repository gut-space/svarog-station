from . import noaa_apt
from . import meteor_qpsk
from . import noaa_apt_gr
from . import satdump

# Each pipeline should be registered in this dictionary
pipelines = {
    'noaa-apt': noaa_apt.execute,
    'noaa-apt-gr': noaa_apt_gr.execute,
    'meteor-qpsk': meteor_qpsk.execute,
    'satdump': satdump.execute
}

__all__ = ["pipelines"]

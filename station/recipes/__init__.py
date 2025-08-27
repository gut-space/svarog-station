import recipes.noaa_apt
import recipes.meteor_qpsk
import recipes.noaa_apt_gr
import recipes.satdump

# Each recipe should be registered in this dictionary
recipes = {
    'noaa-apt': recipes.noaa_apt.execute,
    'noaa-apt-gr': recipes.noaa_apt_gr.execute,
    'meteor-qpsk': recipes.meteor_qpsk.execute,
    'satdump': recipes.satdump.execute
}

__all__ = ["recipes"]

'''
The different satellites require different software and configuration.
This is a recipe-based solution. "Recipe" is a script which is responsible
for the signal reception and its decoding.

Each recipe takes three parameters:

* Working directory - it is writable, clean and temporary directory.
* Frequency - transmission frequency in MHz
* Duration - after this time script should stop SDR, in seconds

As output the script returns a dictionary where key is a category
and value is a path or paths to file(s). Currently the following categories
are supported:
- "signal" for initial audio file in WAV format
- "product" for decoded image
- "log" for detailed decoding notes

In the future additional categories will be added. Most likely there will be:
- "waterfall" presenting the frequency spectrum changing over time
- "telemetry" for any decoded telemetry data

Other categories are likely to appear.

User should have a possibility to execute recipe in stand alone mode, i.e. without
the whole station code (without any need to initialize the station).

Recipe isn't responsible for clean up. The working directory should be deleted
after file processing. If some files should be kept, then they should be moved
to a safe place.

User has a possibility to select recipe by "recipe" parameter in satellite
config. Now it is optional and script try to deduce recipe based on satellite.
(For example if recipe isn't provided and name starts with NOAA then we use
recipe for NOAA).

All recipes must be located in directory with this file ("recipes") and have
"execute" method which accept all parameters.
'''

import datetime
import os
import sys
import logging
from typing import Iterable, List, Tuple

from utils.models import SatelliteConfiguration
from recipes import recipes
from utils.configuration import open_config

if sys.version_info[0] == 3 and sys.version_info[1] >= 8:
    from typing import Literal
else:
    from typing_extensions import Literal


# Categories of result the reception
# Signal - recorded signal (recommended in WAV file)
# Product - binary file decoded from signal (now it is always PNG file)
# Log - logs generated by various tools, such as rx_fm or svarog.
ReceptionResultCategory = Literal["signal", "product", "log"]


def setup_base_dir():
    config = open_config()
    base_dir = config.get("obsdir")
    if base_dir is None:
        base_dir = "/tmp/observations_tmp"
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def get_recipe(sat: SatelliteConfiguration):
    '''
    Returns path to recipe file assigned with the specified satellite.
    If recipe doesn't exist throw LookupError.

    Function check "recipe" field in passed configuration for recipe.
    If it is empty then check built-in list with compatible recipes.
    '''
    recipe = None
    if "recipe" in sat:
        recipe = sat["recipe"]
    if recipe is None and sat["name"].startswith("NOAA"):
        recipe = "noaa-apt"
    if recipe is None:
        raise LookupError("Unknown recipe")

    return recipes[recipe], recipe


def get_unique_dir(sat: SatelliteConfiguration, los: datetime.datetime) -> str:
    '''
    Generates unique, but meaningful dir name.
    '''
    return los.strftime("%Y-%m-%d-%H%M") + "-" + sat["name"].lower().replace(" ", "-")


def get_dir(sat: SatelliteConfiguration, los: datetime.datetime) -> str:
    base_dir = setup_base_dir()

    reception_dir = os.path.join(base_dir, get_unique_dir(sat, los))
    logging.info("Recipe will store all files in %s" % reception_dir)
    os.makedirs(reception_dir, exist_ok=True)

    return reception_dir


def execute_recipe(sat: SatelliteConfiguration, los: datetime.datetime) \
        -> Tuple[Iterable[Tuple[ReceptionResultCategory, str]], str, dict]:
    '''
    Execute recipe for specified satellite and return results.

    Return collection of tuples with category, path, and metadata.
    Second item in result is path to temporary observation directory.
    If no recipe found then throw LookupError.

    We use "signal" category for raw, unprocessed received signal file
    and "product" for finished data (e. q. imagery) extracted from signal.
    You may get multiple files with the same category.

    Caller is responsible for cleaning up the results.
    You need delete or move returned files when you don't need them. You should
    also delete the temporary observation directory.
    '''
    recipe_function, recipe_name = get_recipe(sat)

    reception_dir = get_dir(sat, los)
    now = datetime.datetime.utcnow()
    record_interval = los - now

    metadata = {
        "frequency": sat["freq"],
        "recipe": str(recipe_name)
    }

    output = recipe_function(reception_dir, sat["freq"], record_interval)
    return output, reception_dir, metadata


def get_recipe_names() -> List[str]:
    '''Returns all recipe names.'''
    return list(recipes.keys())

[doc](../README.md) > Installation

This system consists of two elements: station (which is intended to run on a Raspberry Pi with an SDR dongle, but can
be run on any Linux box) and a server (which is intended to be run in a place with good uplink connectivity). If
you are interested in running your own station, you most likely want to deploy just the station and use existing
server. Please contact someone from the Svarog team and we'll hook you up.

## Station installation

You need to install [Rasbian](https://www.raspbian.org/) on your Raspberry Pi. Please follow any Raspbian installation
instruction, such as [this one](https://www.raspberrypi.org/documentation/installation/installing-images/). Once
done, connect to your Pi and do the following as root:

1. **Install necessary dependencies**:

```shell
sudo apt update
sudo apt upgrade
sudo apt install python3-minimal git rtl-sdr airspy sox imagemagick
```

Also, the following tools are needed:

  1. noaa-apt - download Raspberry Pi binaries from https://noaa-apt.mbernardi.com.ar/download.html
  2. medet - https://github.com/artlav/meteor_decoder, binaries available from: http://orbides.org/page.php?id=1023
  3. meteor-demod - https://github.com/dbdexter-dev/meteor_demod

2. **Create svarog user (optional)**

```shell
# useradd svarog
```

3. **Switch to the svarog user (optional)**

```shell
su - svarog
```

4. **Get the latest svarog code**

This and following steps should be done as the user you want to run
the process:

```shell
git clone https://github.com/gut-space/svarog-station
```

5. **Install python dependencies**:

```shell
cd svarog/station
pip3 install --upgrade pip
pip3 install -r requirements.txt
python3 setup.py --skip-python
```

This step will install necessary dependencies. Alternatively, you skip the `install -r requirements.txt` and do `python3 setup.py install` instead, but it will only work in virtual environment.

If you encounter an error similar to this when running the `station` command:

```
ImportError: libcblas.so.3: cannot open shared object file: No such file or directory
```

You may want to also install `libatlas3-base` with the following command:

```shell
sudo apt install libatlas3-base
```

One of the useful setup actions conducted is defining a convenience alias. Instead of typing
`python3 station/cli.py` every time, you can simply type `station` instead.

6. **Station management**

There is a command line tool used to manage the station. You can run it with:

```
$ station
usage: svarog [-h] {clear,logs,plan,pass,config,metadata} ...

positional arguments:
  {clear,logs,plan,pass,config,metadata}
                        commands
    clear               Clear all scheduled reception events
    logs                Show logs
    plan                Schedule planned reception events
    pass                Information about passes
    config              Configuration
    metadata            Displays metadata

optional arguments:
  -h, --help            show this help message and exit
```

You can use it to inspect your configuration, clear or schedule upcoming transmissions.

7. **Tweak your config**.

Run the cli command first:
```
station
```

It will create a tempate config for you. The config file is stored in `~/.config/svarog/config.yml`. The recommended way of tweaking it is to use the cli.py command itself. For example, to set up your location, you can do:

```
station config location -lat 54.34 -lng 23.23 -ele 154
```

In particular, you may want to increase logging level to debug, to spot any problems:

```shell
station config logging --level DEBUG
```

Once your station operates smoothly, you may trim this down to INFO, WARNING or even ERROR.

8. **Schedule observations**

Once your station coordinates are set, you can tell Svarog to schedule observations:

```
station plan --force
```

This should be done once. CLI will update the crontab jobs and will periodically (at 4am each day) add new ones. The `--force` command will conduct the scheduling now, rather than wait for 4am to do scheduling.

**NOTE**: If you installed the tools being used (noaa-apt, medet, meteor-demod) in non-standard locations, please make sure the PATH is set in the crontab. You can set it by using `crontab -e` command and adding a line `PATH=...`. See this nice explanation: https://stackoverflow.com/questions/10129381/crontab-path-and-user

9. **Tweak metadata**

Metadata is set of additional parameters that describe your station. Typically these
are parameters like type of SDR, antenna brand and type, maybe filters or LNA you're using,
but this may be basically anything that you find important enough to be recorded.

A good example of non-standard thing would be the antenna orientation. You may tweak it
and then let the Svarog record observations. Later, you may turn it to some other
position and after a while compare results.

To generate the template to fill in use the following command:

```
python station/cli.py metadata
```

It will print the location of the file (`~/.config/svarog/metadata.json`) and its content. Feel
free to tweak it as you see fit. You may want to add extra data. Any other type will be accepted
as long as it's a valid JSON. Also, take a look at [submit_obs.py](submit_obs.md), which explains
what the parameters mean. Some additional parameters are set by the Svarog station on its own.

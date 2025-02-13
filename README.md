# Svarog ground station

![pylint](https://github.com/gut-space/svarog-station/actions/workflows/pylint.yml/badge.svg)
![flake8](https://github.com/gut-space/svarog-station/actions/workflows/flake8.yml/badge.svg)
![python 3.11](https://github.com/gut-space/svarog-station/actions/workflows/pytest-3.11.yml/badge.svg)
![python 3.12](https://github.com/gut-space/svarog-station/actions/workflows/pytest-3.12.yml/badge.svg)
![CodeQL](https://github.com/gut-space/svarog-station/actions/workflows/github-code-scanning/codeql/badge.svg)

<img align="right" width="128" height="128" src="https://github.com/gut-space/svarog/blob/master/doc/logo.png">

This is the code for a fully functional automated VHF satellite ground station. It can operate on it own,
but can also upload observations to the [Svarog server](https://github.com/gut-space/svarog-server).


The goal of this project is to build a fully functional automated VHF satellite ground station, loosely based on [satnogs](https://satnogs.org) project.

Project founders: [Sławek Figiel](https://github.com/fivitti) and [Tomek Mrugalski](https://github.com/tomaszmrugalski/)

## Project status

As of Feb 2021, the following features are working:

- WiMo TA-1 and QFH antennas, SDR and RPi4 are working
- Automated reception and transmission decoding for NOAA-15, NOAA-18 and NOAA-19 satellites (APT)
- Support for Meteor M2 transmissions (LRPT)
- Transmissions are decoded and uploaded automatically to our content server (see https://svarog.space)
- Automated updates for the server and station
- Orbital TLE data is recorded and prestend in several formats (native TLE, easy to understand orbital parameters etc.)
- Pass over charts (azimuth/elevation)

Work in progress and plans for the near future:

- quality assessment for decoded images
- user management
- georeferencing
- telemetry reception

## Documentation

- [Installation](doc/install.md)
- [Architecture](doc/arch.md)
- [Developer's guide](doc/devel.md)

For older files see https://github.com/gut-space/satnogs.

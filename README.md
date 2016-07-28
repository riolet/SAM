# SAM - System Architecture Mapper

SAM is a tool designed to map a network based on the data log of a router.
It runs as a local python-based server and displays the a map and statistics on the browser.

## Prerequisites

MySQL - SAM will support other databases in the future:

    apt-get install mysql-server
    apt-get install libmysqlclient-dev

Python - python-dev is needed to build the MySQLdb package

    apt-get install python
    apt-get install python-dev

Pip - _optional_, but convenient for installing python packages

    apt-get install python-pip

nfdump - _optional_, for importing Cisco binary NetFlow dumps

    apt-get install nfdump

## Installation

1. Clone the repository
2. Run `pip install -r requirements.txt` from within the directory. (Or do so manually--See text file for package names)
3. Duplicate `dbconfig.py` as `dbconfig_local.py` and fill out database credentials
3. Run `setup.py` from command line

## Usage

1. Import log files into database by any combination of the following methods:
   1. Palo Alto logs: `import_paloalto.py <file>`. The paloalto system log format is expected.
   2. nfdumps: `import_nfdump.py <file>` Binary files from **nfcapd** are expected. nfdump must be installed.
2. Run the preprocessing script `python preprocess.py` to analyze and organize the data

3. Start the server locally by running: `python server.py`

4. Navigate your browser to localhost:8080 and use your mouse to explore the network map

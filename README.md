# SAM - System Architecture Mapper

SAM is a tool designed to map a network based on the data log of a router.
It runs as a local python-based server and displays the a map and statistics on the browser.

Check out the [website](http://sam.centralus.cloudapp.azure.com) for details about the project and a demo!

## Prerequisites

MySQL - SAM will support other databases in the future:

    apt-get install mysql-server
    apt-get install libmysqlclient-dev

Python - python-dev is needed to build the MySQLdb package

    apt-get install python
    apt-get install python-dev

Pip - for installing python packages

    apt-get install python-pip

## Installation

1. Clone the repository
2. Run `pip install -r requirements.txt` from within the directory to install necessary packages.
3. Duplicate `dbconfig.py` as `dbconfig_local.py` and fill out database credentials

## Usage

1. Create a Data source to receive your data in the settings page, or use the default.

2. For static analysis, import your log files into the database by running the following scripts, where log_file is the path to your log file and destination is the name of the data source you wish to fill.

      `python -m importers.import_* <log_file> <destination>`
      
      `python preprocess.py <destination>`
      
      Log formats currently supported include:
   1. Palo Alto logs: The [paloalto syslog](https://www.paloaltonetworks.com/documentation/61/pan-os/pan-os/reports-and-logging/syslog-field-descriptions.html) format is expected.
   2. nfdumps: Binary files from **nfcapd** are expected. nfdump must be installed.
   3. Cisco ASA logs: Partial support. Thanks to Emre for contributing. 
   4. AWS VPC Flow logs: Partial support. Thanks to Emre for contributing. [VPC log spec](http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/flow-logs.html#flow-log-records)
   5. tcpdump: Partial support.
   6. TShark: Partial support.

   Import from all files before going to step 4

3. For live analysis, 
   1. configure your server settings (generate a key for secure upload)
   2. configure your local live_collector (default.cfg) to use the secret code and format, and listen on a host:port.
   3. run `python live_collector.py` to start your collector listening to a socket
   4. direct your router log files to write lines to that socket. (e.g. localhost:514)
   

4. Start the server locally by running: `python server.py`

5. Navigate your browser to localhost:8080/map and use your mouse to explore the network map

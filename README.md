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

1. Edit your defaults.cfg (or export environment variables) to provide your database password to the server. 

2. Create a data source to use in the settings page, or use the default empty data source provided.

3. For static analysis, import your log files into the database by running the following scripts, where log_file is the path to your log file and destination is the name of the data source you wish to fill.

      `python -m importers.import_* <log_file> <destination>`
      
      `python preprocess.py <destination>`
      
      Log formats currently supported include:
   1. Palo Alto logs: The [paloalto syslog](https://www.paloaltonetworks.com/documentation/61/pan-os/pan-os/reports-and-logging/syslog-field-descriptions.html) format is expected.
   2. nfdumps: Binary files from **nfcapd** are expected. nfdump must be installed.
   3. Cisco ASA logs: Partial support. Thanks to [Emre Saglam](https://github.com/emresaglam) for contributing. 
   4. AWS VPC Flow logs: Partial support. Thanks to [Emre Saglam](https://github.com/emresaglam) for contributing. [VPC log spec](http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/flow-logs.html#flow-log-records)
   5. tcpdump: Partial support.
   6. TShark: Partial support.

   Import from all files before moving on.

4. For live analysis, 
   1. On the settings page, choose a data source for your live data to be funneled into then create a Access Key.
   2. Edit default.cfg: Enter your access key into default.cfg in the [live] section.
      also in the live section, choose your format and ports to use.
   3. Start the live update server 
      * The command is `python live_wsgiserver 8081`
      * It should print "http://0.0.0.0:8081/" or similar
   4. Start the collector
      * The command is `python live_collector`
      * You will need priviledges to bind to system port 514.
      * It should print "Testing connection... Succeeded.  Live Collector listening on localhost:514." or similar
   5. Tell your router to output it's log files to that freshly opened socket.
   
5. Start the server locally by running: `python server.py`  For a more robust deployment, SAM supports the WSGI interface (`wsgiserver.py`) and can be run through a different web server.

6. Navigate your browser to localhost:8080 and explore your network!

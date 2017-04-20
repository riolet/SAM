# SAM - System Architecture Mapper

SAM is a tool designed to map a network based on the data log of a router.
It runs as a local python-based server and displays the a map and statistics on the browser.

Check out the [website](http://www.samapper.com) for details about the project and a demo!

## Quickstart (using pip)

install SAM with pip:

    pip install samapper
    
Collect network data with tcpdump and run the http server:

    sudo tcpdump -i any -f --immediate-mode -l -n -Q inout -tt | samapper --local --whois --format=tcpdump
    
  * tcpdump will probably need to be run with sudo to allow it to capture network traffic from your devices.
  * Only tcpdump format works locally via pipe at the moment.

Or, run the http server without collecting data:

    samapper --local --whois --format=none


#### Known issue:
When running samapper in local mode using sqlite (the default) the database will sometimes 
lock up when the collector is inserting and you are viewing the display. If this is happening,
just run the collector for a while, stop it, and run the http server on its own.


## Installation (using git)

### Prerequisites
(optional) mysql - database software that will work better for this than sqlite.

    apt-get install mysql-server libmysqlclient-dev python python-dev
    
pip - to install python packages

    apt-get install python-pip

### Installing
1. Clone this repository
2. Run `pip install -r requirements.txt` from within the directory to install necessary packages.
3. Set environment variables for credentials and settings.  See sam/default.cfg.

```bash
e.g:
export SAM__DATABASE__DBN=mysql
export SAM__DATABASE__USER=root
export SAM__DATABASE__PW=mypassword
```

### Usage

1. Start the server locally by running: `python -m sam.launcher --target=webserver`  For a more robust deployment, SAM supports the WSGI interface (`python sam/server_webserver.py`) and can be run through a different web server.

2. Create a data source to use in the settings page, or use the default empty data source provided.

3. For static analysis, import your log files into the database by running the following scripts, where log_file is the path to your log file and destination is the name of the data source you wish to fill.

      `python -m sam.launcher --target=import --format=<format> --dest=<destination> <log_file>`
      
      Log formats currently supported include:

   1. paloalto: The [paloalto syslog](https://www.paloaltonetworks.com/documentation/61/pan-os/pan-os/reports-and-logging/syslog-field-descriptions.html) format is expected.
   2. nfdump: Binary files from **nfcapd** are expected. nfdump must be installed.
   3. asa: Cisco ASA logs, Partial support. Thanks to Emre for contributing. 
   4. aws: AWS VPC Flow logs: Partial support. Thanks to Emre for contributing. [VPC log spec](http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/flow-logs.html#flow-log-records)
   5. tcpdump: Designed to work with live local mode. See quickstart above
   6. tshark: Partial support.

4. For live analysis,
 
   1. On the settings page, choose a data source for your live data to be funneled into then create a Access Key
   2. Edit default.cfg or set an environment variable (SAM__COLLECTOR__UPLOAD_KEY) to your new access key
   3. Start the aggregator (this loads log data into the database) 
      * `python -m sam.launcher --target=aggregator`
   4. Start the collector (this listens to port 514 and translates syslog lines)
      * `python -m sam.launcher --target=collector`
      * You will need priviledges to bind to system port 514.
      * It should print "Testing connection... Succeeded." 
   5. Tell your router to output it's log files to that freshly opened socket.

5. Navigate your browser to localhost:8080 and explore your network!

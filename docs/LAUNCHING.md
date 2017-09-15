# How To ...

This is a collection of directives for using SAM.  Some environment variables have 
equivalent invocation flags. Environment variables are given preference 
in this document.

All environment variables can be found in sam/default.cfg.
```
[section]
key1 = value1
# comment
key2 = value2
```
The above can be overridden with environment set as follows:
```bash
export SAM__SECTION__KEY1=value1
export SAM__SECTION__KEY2=value2
```


# Run SAM
The basic command depends on if you have cloned the repository or installed via pip.

If one has the repo, commands are executed as `python sam/launcher.py ...`

If one has the pip package samapper, commands are executed as `samapper ...`

## Run the webserver locally:

It is strongly advised to install mysql for running SAM.

`apt-get install python-dev mysql-server libmysqlclient-dev`

Common environment variables:
* `export SAM__DATABASE__DBN=mysql` (database engine. mysql or sqlite)
* `export SAM__DATABASE__DB=samdb`  (database name)
* `export SAM__DATABASE__USER=root` (database access username)
* `export SAM__DATABASE__PW=mypass` (database access password)
* `export SAM__WEBSERVER__LISTEN_PORT=8080`

`python sam/launcher.py --target=webserver`

## Install plugins
Given that plugins 'plugin1' and 'plugin2' have been placed in the folder '/opt/sam/plugins',
configure your environment as follows:

* `export SAM__PLUGINS__ROOT=/opt/sam/plugins`
* `export SAM__PLUGINS__ENABLED=ALL` (or comma-separated `...=plugin1,plugin2` or a single plugin `...=plugin2`)

`python sam/launcher.py --target=webserver`

## Run on a server
SAM exposes the WSGI interface. Server software such as apache and nginx can support wsgi applications.

sam/server_webserver.py works as a WSGI endpoint
sam/server_aggregator.py works as a WSGI endpoint

Complete server setup instructions are beyond the scope of this document, but the 
webpy [cookbook pages](http://webpy.org/cookbook/) and 
[deployment page](http://webpy.org/deployment) provides several examples. 

#Collectors and Aggregators
SAM is designed for receiving continuous input. The external devices send packets of traffic data to SAM's collectors, SAM's collectors send uniform traffic data to aggregators, and aggregators insert that data into the database.

**Collectors** are meant to be light and deployed wherever needed to receive traffic, simplify it, and forward it to the server.

**Aggregators** live on the server with the database and the webserver.

**Webservers** interact with the db and present web pages to your browser.

## Deploying a collector pipeline locally

1. Start up a webserver
   1. `export SAM__WEBSERVER__LISTEN_PORT=8080` 
   1. `python sam/launcher.py --target=webserver`
1. Navigate your browser to http://localhost:8080
1. Open the **Settings** page
   1. In the **Live Updates** section, click the generate button to get an access key. Write this down.
1. Start up the aggregator
   1. `export SAM__AGGREGATOR__LISTEN_PORT=8081`
   1. `python sam/launcher.py --target=aggregator`
1. Start up the collector
   1. `export SAM__COLLECTOR__LISTEN_HOST=`  (leave blank)
   1. `export SAM__COLLECTOR__LISTEN_PORT=514`  (use the port you expect to receive traffic logs on. Note: binding to system ports (<1024) will require privileged execution)
   1. `export SAM__COLLECTOR__TARGET_ADDRESS=http://localhost:8081`  (the address of the aggregator)
   1. `export SAM__COLLECTOR__UPLOAD_KEY=abc123def456`  (the access key you generated earlier)
   1. `export SAM__COLLECTOR__FORMAT=asasyslog`  (the format you expect to receive)
   1. `python sam/launcher.py --target=collector`

It will be visible in stdout of the collector and aggregator when traffic has been received and processed.
Nothing will be visible in the webserver until the aggregator has done processing on its first buffer of traffic. 

#Import Data

##Import Log Files
Importing palo alto syslog file:

`python sam/launcher.py --target=import --format=paloalto [--dest=default] /path/to/syslog.log`

Where optional argument dest refers to the name of the data source to import in to. 
The same method applies to files of other formats:

```bash
# asa syslog
python sam/launcher.py --target=import --format=asasyslog /path/to/asa.log
# netflow log
python sam/launcher.py --target=import --format=netflow /path/to/nfcapd.1355764892
# tcpdump
python sam/launcher.py --target=import --format=tcpdump /path/to/tcpdump.log
# tshark
python sam/launcher.py --target=import --format=tshark /path/to/tshark.pcap
```

## Use Live Local Data

The following pipes collection of local traffic via tcpdump directly into sam, and enables WHOIS lookup on the IPs. 
After collecting for a minute or two, the traffic will be visible at localhost:8080.
Note that network traffic collection is perfomed with elevated priviledges.

```
sudo tcpdump -i any -f --immediate-mode -l -n -Q inout -tt | python sam/launcher.py --local --whois --format=tcpdump
# data collection can be omitted of you just wish to view what was previously collected:
python sam/launcher.py --local
```

Please note that syntax for tcpdump may be slightly different on your own machine. 
The desired output format includes numeric unix timestamp, numeric IP address, numeric port

Also possible is the use of tshark:

```
sudo tshark -E separator=@ -e frame.number -e frame.time -e ip.src -e tcp.srcport -e udp.srcport -e ip.dst -e tcp.dstport -e udp.dstport -e frame.len -T fields | python sam/launcher.py --local --format=tshark
```

By default, --local mode uses sqlite and a temporary db file. This is controlled by environment variables prefixed with `SAM__LOCAL__`

`export SAM__LOCAL__DBN=sqlite`
`export SAM__LOCAL__DB=/tmp/sam_local.db`

## Collect Syslog and Netflow data from Cisco ASA

Instructions are provided for Syslog and Netflow using the ASDM. Please refer to Cisco's support 
and documentation to enable logging via CLI.

### Syslog

1. Open the **Configuration** tab (top left)
1. Open the **Device Management** category (bottom left)
1. Expand the **Logging** tree-view folder (left)
1. Choose **Event Lists** tree-view item
1. Add an event list called _TrafficEvents_
   1. Leave Event Class / Severity empty
   1. Add IDs to the Message IDs list:
      1. 106100
      1. 106015
      1. 106023
      1. 313008
      1. 302013-302018
      1. 302020-302021
      1. 313001
      1. 710003
   1. Click **OK** to complete list creation
1. Choose **Logging Filters** tree-view item
1. Edit the “Syslog Servers” row
   1. Set “Syslogs from All Event Classes” to use event list _TrafficEvents_
   1. Click **OK** to complete edits
1. Choose the **Syslog Servers** tree-view item
1. Add a new entry:
   1. Interface: inside (if your logging machine is in your internal network)
   1. IP Address: your collector machine’s address
   1. Protocol: UDP
   1. Port: 5140
1. Choose the **Logging Setup** tree-view item
1. Check the “Enable logging” box
1. **Apply** and **Save**

1. Now is time to test your settings. In a terminal on the syslog-receiving machine:
   1. `nc -lku 5140`
   1. This should show syslog messages in the console.
   1. Ctrl-C to stop listening.
1. Set environment variables:
   * `export SAM__COLLECTOR__LISTEN_PORT=5140`
   * `export SAM__COLLECTOR__LISTEN_HOST=`
   * `export SAM__COLLECTOR__UPLOAD_KEY= <found in webserver settings>`
   * `export SAM__COLLECTOR__FORMAT=asasyslog`
1. Start collector: `python sam/launcher.py --target=collector`


### Netflow

The following instructions largely duplicate the descriptions given [here (cisco.com)](https://supportforums.cisco.com/t5/security-documents/configuring-netflow-on-asa-with-asdm/ta-p/3119466).

1. Open the **Configuration** tab (top left)
1. Open the **Device Management** category (bottom left)
1. Expand the **Logging** tree-view folder (left)
1. Choose **NetFlow** tree-view item
   1. Add a collector
   1. Interface: inside
   1. IP Address or Hostname: Your IP or hostname
   1. UDP Port: 5140 or port of your choice not currently in use. 
   1. **OK** to complete Add process.
   1. [_Optional_] Set the Template Timeout Rate to 5 minutes
1. Open the **Firewall** category (bottom left)
1. Choose the **Service Policy Rules** tree-view item
   1. **Add** a new rule
   1. Choose **Global** radio button
   1. On the next page, select **Source and Destination IP Address** as your Traffic Match Criteria
   1. On the next page, pick:
      1. Action: Match
      1. Source: any
      1. Destination: any
      1. Service: ip
   1. On the next page, choose **Torn Down** for Flow Event Type and ensure your collector has a checkmark for the send column.
1. **Apply** changes and **Save**
1. Test settings:
   1. record data with:  
   1. `nfcapd -T all -l <log_directory> -p <port>`
   1. translate data with: 
   1. `nfdump -r <log_file_or_directory> -b -o "fmt:%pr,%sa,%sp,%da,%dp,%ts,%ibyt,%obyt,%ipkt,%opkt,%td"`
1. Set environment and start collector:
   1. `export SAM__COLLECTOR__UPLOAD_KEY= <found in webserver settings>`
   1. `python sam/launcher.py --target=collector --format=netflow --port=8787`

Note: NetFlow traffic packets cannot be interpreted by the receiver until the source has sent the appropriate templates. This means that netflow data may not appear to work over short durations. The default template transmission repeat time for a Cisco ASA 5505 is every 30 minutes.

# Security Rules

One default rule is provided to identify traffic to compromised hosts. Additional rules can be created or customized.

## Adding a rule

## Editing a rule

## Advanced Custom rules

TODO: can we create a template that lets you put in your pattern to match?

## Creating a rule template

## Reapplying existing rules

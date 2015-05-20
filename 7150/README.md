
BurstMonitor
============

The Interface Burst Monitor (IBM) observes the maximum bit rate of interfaces and records bursts of traffic on either the RX or TX side of the interface.

The solution is composed of two components:
 - **IBM data collector** - responsible for collecting the burst information to CSV files on the local disk
 - **IBM simAPI plugin** - is responsible for exposing the burst information via eAPI (https://github.com/arista-eosplus/simAPI/tree/ibm)

##Installation

 - if another extension with the same name is already installed, first remove that:
```
EOS# show extensions
Name                                       Version/Release           Status extension
------------------------------------------ ------------------------- ------ ----
ibm-<version>.swix                         <version>/<release>       A, I      1
...
A: available | NA: not available | I: installed | NI: not installed | F: forced

EOS# no extension ibm-<version>.swix
EOS# show extensions
show extensions
Name                                       Version/Release           Status extension
------------------------------------------ ------------------------- ------ ----
simApi-<version>.rpm                       <version>/<release>       A, NI     1

A: available | NA: not available | I: installed | NI: not installed | F: forced

EOS# delete extension:ibm-<version>.swix
EOS# show extensions
No extensions are available

EOS# copy installed-extensions boot-extensions
Copy completed successfully.
```
 - copy the extension to the switch using the **copy** command:
```
EOS# copy https://github.com/arista-eosplus/BurstMonitor/raw/master/7150/ibm-<version>.swix extension:
```
 - install the extension:
```
EOS# extension ibm-<version>.swix
```
 - in order to make the extension persistent over reboot, use:
```
EOS# copy installed-extensions boot-extensions
```
If everything went well, **show extensions** should show:
```
EOS#show extensions 
show extensions
Name                                       Version/Release           Status extension
------------------------------------------ ------------------------- ------ ----
ibm-<version>.swix                         <version>/<release>        A, I     2

A: available | NA: not available | I: installed | NI: not installed | F: forced
```

##Configuration 

####Switch configuration

In order to start the **IBM data collector**, add the following to the running-config:
```
daemon ibm
   exec /usr/bin/python /persist/sys/ibm/ibm
   no shutdown
```
For **IBM simAPI plugin** to work, remeber to enable eAPI on the switch:
```
management api http-commands
   no shutdown
```
In order to make the solution boot-persistant, run *copy runnning-config startup-config* once everything is set up.

####IBM data collector

The data collector config file is */persist/sys/ibm/ibm.json*. Here is an example:

```
{
   // Set of interfaces to monitor.                            
   // e.g.                                                     
   //   "interfaces" : [ "Ethernet1",                          
   //                    "Ethernet2" ],                        
   "interfaces" : [
       "Ethernet1",
       "Et2",
   ],                                                          

   // Number of hardware polling intervals to report together  
   // default: 1000                                            
   "batch_size" :  1000,

   // Where to store the log files for all interfaces          
   // default: /tmp/ibm                                        
   "log_dir" : "/tmp/ibm",

   // Number of log files to keep in memory for each interface 
   // default : 3                                              
   "log_files" : 3,

   // Number of entries to keep in each file                   
   // default : 100                                            
   "log_entries" :  100
}
```
Any changes made to the configuration file will require a restart of the data collector daemon in order to take effect.
```
(config)# daemon ibm
(config-daemon-ibm)# shutdown
(config-daemon-ibm)# no shutdown
```
IBM will poll the hardware counters as fast as possible and will record the link utilization for each polling interval. A batch of polling intervals are grouped together for reporting purposes - this is controlled by the *batch_size* option from above. In the example from above, every 1000 consecutitive polling intervals, IBM will record the *maximum RX/TX burst* of traffic from all the polling intervals in the batch (in CSV format). 

Note that the *maximum RX/TX burst* is computed with respect to the link speed and NOT only the number of Bytes which are received/transmitted during a polling interval. Hence, both the size (in Bytes) and length (in us) of a polling interval are considered in order to compute the maximum burst. 

Here is an example:
```
index,batch_rx(B),batch_tx(B),batch_start,batch_duration(ms)max_rx_burst(B),rx_burst_perc,max_rx_burst_start(us),rx_burst_duration(ms),max_tx_burst(B),tx_burst_perc,max_tx_burst_start(us),tx_burst_duration(ms)
1,0,0,2474012551,156.041,0,0.000,2474167056,1.536,0,0.000,2474167056,1.536
```
The recorded data for each interface can be found in **/tmp/ibm/\<INTERFACE_NAME\>**. For each interface, IBM will store multiple log files (named **/tmp/ibm/\<INTERFACE_NAME\>/1**, **/tmp/ibm/\<INTERFACE_NAME\>/2**, **/tmp/ibm/\<INTERFACE_NAME\>/3**, ...) and the maximum number of such files is cofigured via the *log_files* option. Each log file wil contain up-to *log_entries* entries.

Whenever the first log file for each interface (**/tmp/ibm/\<INTERFACE_NAME\>/1**) becomes full (meaning that the number of recorded entries in the file equals the *log_entries* option in the config file), the log files for that interface are rotated as follows:
 - **/tmp/ibm/\<INTERFACE_NAME\>/1** -> **/tmp/ibm/\<INTERFACE_NAME\>/2**
 - **/tmp/ibm/\<INTERFACE_NAME\>/2** -> **/tmp/ibm/\<INTERFACE_NAME\>/3**
 - ...
 - **/tmp/ibm/\<INTERFACE_NAME\>/\<log_files-1\>** -> **/tmp/ibm/\<INTERFACE_NAME\>/\<log_files\>**

####simAPI plugin

The simAPI config file is */persist/sys/simAPI/simApi.json*. The required IBM configuration is highlighted below:
```
{
  "cmds" : {
  },

  "regexes" : {
     "ibm (.*)": { "plugin": "ibm" }        // <-----------
  }
}
```
Note that if IBM is installed via the SWIX file in this repository, or the RPM under *https://github.com/arista-eosplus/simAPI/tree/ibm* is being used, then the above configuration will be the default one. Otherwise, the section highlighted above must be added to the simAPI configuration file (and the *ibm* plugin must be installed under */persist/sys/simAPI/plugins*).

##Output

####IBM data collector

The IBM CSV log files are stored under */tmp/ibm*. Note that the log files are cleared whenever the *IBM data collector* is restarted (either manually via the configuration of the switch, or automatically in case of a crash). Here is an example:

```
(bash)# cat /tmp/ibm/Ethernet10/1
index,batch_rx(B),batch_tx(B),batch_start,batch_duration(ms),rx_burst(B),rx_burst_perc,rx_burst_start(us),rx_burst_duration(ms),tx_burst(B),tx_burst_perc,tx_burst_start(us),tx_burst_duration(ms)
1,0,0,16681780490,6499.542,0,0.000,4377302265,6.554,0,0.000,4377302265,6.554
2,0,0,16688280032,6516.281,0,0.000,4377302265,6.554,0,0.000,4377302265,6.554
3,0,0,16694796313,6483.009,0,0.000,4377302265,6.554,0,0.000,4377302265,6.554
...
```

####simAPI plugin

The **IBM simAPI plugin** allows for the following CLI commands to be served via eAPI (the following examples will use Python, but same applies for any other programming language or the eAPI Explorer running on the switch):

```
>>>import jsonrpclib
>>>client = jsonrpclib.Server('https://<username>:<password>@<hostname>/command-api')
```
 - **ibm ports** - returns the list of ports which are monitored for bursts (see */persist/sys/ibm/ibm.json*)
```
>>> client.runCmds(1, ['ibm ports'])[0]

['Ethernet1', 'Ethernet10', 'Ethernet11', 'Ethernet12', 'Ethernet2', 'Ethernet3', 'Ethernet4', 'Ethernet5', 'Ethernet6', 'Ethernet7', 'Ethernet8', 'Ethernet9']
```
 - **ibm Ethernet\<no.\> info** - returns the list of log files available for each interface
    - *start* represents the timestamp for start of the first (oldest) polling interval in the log file
    - *end* represents the timestamp for end of the last (newest) polling interval in the log file
    - *entries* represents the number of entries in the file
    - *free* represents the number of additional entries which could be added to the file, before the log files corresponding to that interface will be rotated (only interesting for file no. **1**, for the rest the value will always be **0**)
    - *path* represents the file's path on the local disk 
```
>>> client.runCmds(1, ['ibm Ethernet1 info'])[0]

{'1': {'start': 16681776937, 
        'entries': 96, 
        'end': 17330496870, 
        'free': 4, 
        'path': '/tmp/ibm/Ethernet1/1'}, 
  '3': {'start': 15385032249,
        'entries': 100,
        'end': 16033180921,
        'free': 0,
        'path': '/tmp/ibm/Ethernet1/3'}, 
  '2': {'start': 16033180921, 
        'entries': 100, 
        'end': 16681776937, 
        'free': 0, 
        'path': '/tmp/ibm/Ethernet1/2'}}
```
- **ibm Ethernet\<no.\> files \<no.\>[,\<no.\>]** - returns the entries in the log files
   - CSV format 
```
>>> client.runCmds(1, ['ibm Ethernet1 files 1,2'], 'csv')[0] OR
>>> client.runCmds(1, ['ibm Ethernet1 files 1,2'], 'text')[0]

{'1': 'index,batch_rx(B),batch_tx(B),batch_start,batch_duration(ms),rx_burst(B),rx_burst_perc,rx_burst_start(us),rx_burst_duration(ms),tx_burst(B),tx_burst_perc,tx_burst_start(us),tx_burst_duration(ms)\n1,0,0,17978640249,6466.742,0,0.000,4377298630,6.948,0,0.000,4377298630,6.948\n2,0,0,17985106991,6476.967,0,0.000,4377298630,6.948,0,0.000,4377298630,6.948\n3,0,0,17991583958,6482.583,0,0.000,4377298630,6.948,0,0.000,4377298630,6.948\n4,0,0,17998066541,6491.744,0,0.000,4377298630,6.948,0,0.000,4377298630,6.948\n5,0,0,18004558285,6483.148,0,0.000,4377298630,6.948,0,0.000,4377298630,6.948\n6,0,0,18011041433,6527.965,0,0.000,4377298630,6.948,0,0.000,4377298630,6.948\n7,0,0,18017569398,6488.967,0,0.000,4377298630,6.948,0,0.000,4377298630,6.948\n8,0,0,18024058365,6490.787,0,0.000,4377298630,6.948,0,0.000,4377298630,6.948\n9,0,0,18030549152,6479.035,0,0.000,4377298630,6.948,0,0.000,4377298630,6.948\n10,0,0,18037028187,6472.433,0,0...
'2': 'index,batch_rx(B),batch_tx(B),batch_start,batch_duration(ms),rx_burst(B),rx_burst_perc,rx_burst_start(us),rx_burst_duration(ms),tx_burst(B),tx_burst_perc,tx_burst_start(us),tx_burst_duration(ms)\n1,0,0,...}
```
   - JSON format
      - *batch_start* represented the timestamp (in us) corresponding to beginning of the first polling interval in the batch
      - *batch_duration* represented the total duration (in ms) of all the polling intervals in a batch
      - *batch_rx/tx* represents the total number of Bytes received/transmitted by the interface during the batch
      - *rx/tx_burst* represents the size of the burst (in Bytes)
      - *rx/tx_burst_perc* represents the size of the burst as a % of the maximum link speed
      - *rx/tx_burst_start* represented the timestamp (in us) corresponding to the maximum burst in the batch
      - *rx/tx_burst_duration* represented the total duration (in ms) of the maximum burst in the batch
```
>>> client.runCmds(1, ['ibm Ethernet1 files 1,2'])[0] OR
>>> client.runCmds(1, ['ibm Ethernet1 files 1,2'], 'json')[0]

{'1': {'24': {'batch_duration': '6527.259', 
              'batch_rx': '0', 
              'tx_burst': '0', 
              'tx_burst_perc': '0.000', 
              'rx_burst_perc': '0.000', 
              'rx_burst': '0', 
              'batch_tx': '0', 
              'batch_start': '18127798342', 
              'tx_burst_start': '4377298630', 
              'rx_burst_duration': '6.948', 
              'rx_burst_start': '4377298630', 
              'tx_burst_duration': u'6.948'}, 
        '25': {'batch_duration': u'6480.307', 
               'batch_rx': u'0', 
...
```

**Note** that the CLI commands described above are only available via eAPI and will not be available via the CLI of the switch. For more, see *https://github.com/arista-eosplus/simAPI*.

##Debugging

Here are some tips for debugging IBM issues:
 - check that the extension is installed and properly configured as shown above
 - check that **IBM data collector** is running (the process name is *ibm*). If the collector is not running, check that the daemon is enabled in the config (*no shutdown*).
```
(enable)# bash pgrep ibm
11367
```
 - check whether **IBM data collector** is crashing and being restarted often by looking at syslog and the timestamps of */var/log/agents/ibm\**
 - run the **IBM data collector** manually, in debug mode:
```
(bash)$ sudo /usr/bin/python /persist/sys/ibm/ibm -d
sudo /usr/bin/python /persist/sys/ibm/ibm -d
Verifying the hardware model: DCS-7150S-52-CL
Setting process name to ibm
Loading intf-to-port mapping:...
```
 - in order to debug simAPI plugin issues, first try to see whether eAPI works as expected by running *show version* both locally and remotely
```
(bash)# python
>>>import jsonrpclib
>>>client = jsonrpclib.Server('https://<username>:<password>@<hostname>/command-api')
>>> client.runCmds(1, ['show version'])
```
 - if you still can't sort it out, raise a GitHub issue which includes:
   - the results of the debugging steps from above
   - the output of *show tech-support*
   - the contents of */persist/sys/ibm* and */persist/sys/simAPI* on the switch
   - the contents of */var/log*
   - the contents of */tmp/ibm*

##Compatibility

Version 1.0.0 has been developed and tested against EOS-4.15.0F. This version should also work on EOS versions > EOS-4.15.5F, but is not tested. Please contact eosplus@arista.com if you would like an officially supported release of this software.

##Limitations
The **IBM data collector** works by polling the hardware counters as fast as possible. It will consume up to a maximum of 50% of the CPU resources.

The following configuration changes require a restart of the data collector daemon in order ensure correct behaviour:
 - any changes made to the speed configuration of interfaces being monitored by the IBM (e.g. agile ports) 
 - any updates of the ibm extension
```
(config)# daemon ibm
(config-daemon-ibm)# shutdown
(config-daemon-ibm)# no shutdown
```

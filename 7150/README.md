
BurstMonitor
============

The Interface Burst Monitor (IBM) observes the bit rate of interfaces and records bursts of traffic on either the RX or TX side of each interface.

The solution is composed of two components:
 - **IBM data collector** - responsible for collecting the burst information to CSV files on the local disk
 - **IBM simAPI plugin** - responsible for exposing the burst information via eAPI (see also https://github.com/arista-eosplus/simAPI/tree/ibm)

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
The **IBM simAPI plugin** requires eAPI to be enabled on the switch:
```
management api http-commands
   protocol unix
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
   // default: 100                                            
   "batch_size" :  100,

   // Where to store the log files for all interfaces          
   // default: /tmp/ibm                                        
   "log_dir" : "/tmp/ibm",

   // Number of log files to keep in memory for each interface 
   // default : 3                                              
   "log_files" : 3,

   // Number of entries to keep in each file                   
   // default : 100                                            
   "log_entries" :  100
   
   // Target poll duration for each interface (in ms)
   // default: 30                                    
   "poll_duration" : 30                              
}
```
Any changes made to the configuration file require a restart of the data collection daemon:
```
(config)# daemon ibm
(config-daemon-ibm)# shutdown
(config-daemon-ibm)# no shutdown

OR

(bash)# sudo pkill ibm
```
IBM will poll the hardware counters as fast as the configured by *poll_duration* and will record the link utilization for each polling interval. A batch of polling intervals are grouped together for reporting purposes - this is controlled by the *batch_size* option from above. In the example from above, every 100 consecutitive polling intervals, IBM will record the *maximum RX/TX burst* of traffic from all the polling intervals in the batch (in CSV format). 

Note that the *maximum RX/TX burst* is computed with respect to the link speed and NOT the number of Bytes which are received/transmitted during a polling interval. Hence, both the size (in Bytes) and length (in us) of a polling interval are considered in order to compute the maximum burst. 

Here is an example:
```
index,batch_rx_bytes,batch_tx_bytes,batch_start_ms,batch_duration_ms,burst_rx_bytes,burst_rx_perc,burst_rx_offset_ms,burst_rx_duration_ms,burst_tx_bytes,burst_tx_perc,burst_tx_offset_ms,burst_tx_duration_ms
1,2651178944,0,1.43327791883e+12,3029.877,28375296,70.041,780.039,32.41,0,0.000,0.0,30.19
...
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
index,batch_rx_bytes,batch_tx_bytes,batch_start_ms,batch_duration_ms,burst_rx_bytes,burst_rx_perc,burst_rx_offset_ms,burst_rx_duration_ms,burst_tx_bytes,burst_tx_perc,burst_tx_offset_ms,burst_tx_duration_ms
1,2651178944,0,1.43327791883e+12,3029.877,28375296,70.041,780.039,32.41,0,0.000,0.0,30.19
2,2651290816,0,1.43327792186e+12,3030.005,26744640,71.324,900.061,29.998,0,0.000,0.0,31.736
3,2652512320,0,1.43327792489e+12,3031.399,26862592,71.672,2370.112,29.984,0,0.000,0.0,30.309
4,2650143360,0,1.43327792792e+12,3028.694,27566848,73.156,2848.683,30.146,0,0.000,0.0,29.512
```

####simAPI plugin

The **IBM simAPI plugin** allows for the following CLI commands to be served via eAPI (the following examples will use Python, but same applies for any other programming language or the eAPI Explorer running on the switch):

```
>>> import jsonrpclib
>>> client = jsonrpclib.Server('https://<username>:<password>@<hostname>/command-api')
```

 - **ibm ports** - returns the list of ports which are monitored for bursts (see */persist/sys/ibm/ibm.json*)

```
>>> client.runCmds(1, ['ibm ports'])[0]

['Ethernet1', 'Ethernet10', 'Ethernet11', 'Ethernet12', 'Ethernet2', 'Ethernet3', 'Ethernet4', 'Ethernet5', 'Ethernet6', 'Ethernet7', 'Ethernet8', 'Ethernet9']
```

 - **ibm Ethernet\<no.\> info** - returns the list of log files available for each interface
    - *name* represents the name of the file
    - *entries* represents the number of entries in the file
    - *path* represents the file's path on the local disk 
    - *start_ms* represents the timestamp for start of the first (oldest) polling interval in the log file
    - *end_ms* represents the timestamp for end of the last (newest) polling interval in the log file
    - *free* represents the number of additional entries which could be added to the file, before the log files corresponding to that interface will be rotated (only interesting for file no. **1**, for the rest the value will always be **0**)

```
>>> client.runCmds(1, ['ibm Ethernet1 info'])[0]

[
 {'name': '1', 
  'entries': 66, 
  'path': '/tmp/ibm/Ethernet1/1', 
  'start_ms': 1433277918830.0, 
  'end_ms': 1433278118810.0, 
  'free': 34}, 
  
  {'name': '2', 
   'entries': 100,
   ...
```

- **ibm Ethernet\<no.\> files \<no.\>[,\<no.\>]** - returns the entries in the log files
   - CSV format (the result is actually JSON, but contains the CSV contents of the requested files)
      - *name* represents the name of the file
      - *contents* represents the contents of the file

```
>>> client.runCmds(1, ['ibm Ethernet1 files 1,2'], 'csv')[0] OR
>>> client.runCmds(1, ['ibm Ethernet1 files 1,2'], 'text')[0]

[
 {'name': '1', 
  'contents': 'index,batch_rx_bytes,batch_tx_bytes,batch_start_ms,batch_duration_ms,burst_rx_bytes,burst_rx_perc,burst_rx_offset_ms,burst_rx_duration_ms,burst_tx_bytes,burst_tx_perc,burst_tx_offset_ms,burst_tx_duration_ms\n1,2600746496,230,1.43328157441e+12,2972.223,1505920,70.165,0.0,1.717,230,0.001,992.371,29.959\n2,2654036928,0,1.43328157738e+12,3033.145,26820096,70.535,1231.83,30.419,0,0.000,0.0,30.268\n3,2648707776,0,1.43328158041e+12,3027.052,27087296,72.221,150.603,30.005,0,0.000,0.0,29.871\n4,2654010240,0,1.43328158344e+12,3033.088,27107648,72.095,1143.524,30.08,0,0.000,0.0,30.077\n5,2648487936,0,1.43328158647e+12,3026.827,26478528,70.711,746.865,29.957,0,0.000,0.0,27.755...
  }
  {'name': '2', 
  'contents': 'index,batch_rx_bytes,batch_tx_bytes,batch_start_ms,batch_duration_ms,burst_rx_bytes,burst_rx_perc,burst_rx_offset_ms,burst_rx_duration_ms,burst_tx_bytes,burst_tx_perc,burst_tx_offset_ms,burst_tx_duration_ms\n1,...
...
```

   - JSON format
      - *first_timestamp_ms* represents the timestamp (in ms) corresponding to the beginning of the first polling interval recorded in the file
      - *last_timestamp_ms* represents the timestamp (in ms) corresponding to the end of the last polling interval recorded in the file
      - *name* represents the name of the file
      - for each entry:
         - *batch_start_ms* represented the timestamp (in ms) corresponding to beginning of the first polling interval in the batch
         - *batch_duration_ms* represented the total duration (in ms) of all the polling intervals in a batch
         - *batch_rx/tx_bytes* represents the total number of Bytes received/transmitted by the interface during the batch
         - *burst_rx/tx_bytes* represents the size of the maximum burst (in Bytes)
         - *burst_rx/tx_perc* represents the size of the maximum burst as a % of the maximum link speed
         - *burst_rx/tx_offset_ms* represented the offset (in ms) corresponding to the maximum burst in the batch (from **batch_start_ms**)
         - *burst_rx/tx_duration_ms* represented the duration (in ms) of the maximum burst in the batch
```
>>> client.runCmds(1, ['ibm Ethernet1 files 1,2'])[0] OR
>>> client.runCmds(1, ['ibm Ethernet1 files 1,2'], 'json')[0]

[
 {'last_timestamp_ms': 1433278115780.0, 
  'first_timestamp_ms': 1433277918830.0, 
  'name': '1', 
  'entries': [
     {'index': '1', 
      'burst_rx_bytes': '28375296', 
      'burst_rx_offset_ms': '780.039', 
      'burst_tx_offset_ms': '0.0', 
      'burst_rx_duration_ms': '32.41', 
      'batch_rx_bytes': '2651178944', 
      'batch_duration_ms': '3029.877', 
      'burst_tx_bytes': '0', 
      'burst_tx_perc': '0.000', 
      'batch_start_ms': '1.43327791883e+12', 
      'batch_tx_bytes': '0', 
      'burst_rx_perc': '70.041'}, 
     {'index': '2', 
      'burst_rx_bytes': '26744640', 
      ...
 ```

**Note** that the CLI commands described above are only available via eAPI and will not be available via the CLI of the switch. For more, see *https://github.com/arista-eosplus/simAPI*.

##Debugging

Here are some tips for debugging IBM issues:
 - check that the extension is installed and properly configured as shown above
 - check that **IBM data collector** is running (the process name is *ibm*). If the collector is not running, check that the daemon is enabled in the config (*no shutdown*):
```
(enable)# bash pgrep ibm
11367
```
 - check whether **IBM data collector** is crashing and being restarted often by looking at syslog and the timestamps of */var/log/agents/ibm**
 - run the **IBM data collector** manually, in debug mode:
```
(bash)$ sudo /usr/bin/python /persist/sys/ibm/ibm -d
sudo /usr/bin/python /persist/sys/ibm/ibm -d
Verifying the hardware model: DCS-7150S-52-CL
Setting process name to ibm
Loading intf-to-port mapping:...
```
 - in order to debug simAPI plugin issues, first try to see whether eAPI works as expected by running *show version* both locally and remotely:
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

Version 1.4.0 has been developed and tested against EOS-4.15.0F. This version should also work on EOS versions > EOS-4.15.5F, but is not tested. Please contact eosplus@arista.com if you would like an officially supported release of this software.

##Limitations
The **IBM data collector** works by polling the hardware counters as fast as possible. It will consume up to a maximum of 50% of the CPU resources.

The following configuration changes require a restart of the data collector daemon in order ensure correct behaviour:
 - any changes made to the speed configuration of interfaces being monitored by the IBM (e.g. agile ports) 
 - any updates of the ibm extension
 - any changes made to */persist/sys/ibm/ibm.json*

```
(config)# daemon ibm
(config-daemon-ibm)# shutdown
(config-daemon-ibm)# no shutdown
```

##Extra
####Creating a new SWIX file with a different IBM default configuration

 - clone this repository

```
git clone https://github.com/arista-eosplus/BurstMonitor
cd BurstMonitor/7150
```

 - update *conf/ibm.json*

```
vi conf/ibm.json
```

 - copy *rpmbuild/ibm-\<version\>.rpm* to an Arista switch / vEOS node

```
scp rpmbuild/ibm-<version>.rpm <Arista>:/mnt/flash
```

 - copy the simAPI RPM to the same switch / vEOS node (use the *ibm* branch in the simAPI repository for pre-configured default IBM plugin configuration)

```
Arista(bash)$ cd /mnt/flash
Arista(bash)$ wget https://github.com/arista-eosplus/simAPI/raw/ibm/simApi-<version>.rpm
```

 - create updated SWIX file

```
Arista(bash)$ swix create /mnt/flash/ibm-<version>.swix /mnt/flash/ibm-<version>.rpm /mnt/flash/simApi-<version>.rpm
```

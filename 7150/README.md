
BurstMonitor
============

##Introduction

The Burst Monitor observes the bit rate of interfaces and records bursts of
traffic on either the RX or TX side of each interface. It will records these
bursts and provide the number of bytes that composed the burst along with the
percent utilization of the link during that burst. It monitors the
specified interfaces every N milliseconds (defined in your configuration).
As the number of interfaces monitored increases as well as the polling interval
decreases, the overall CPU usage will increase. There is built-in limiter that
will prevent this process from consuming more than 50% of the system CPU time.
Finally, records will be written in CSV format to a directory in /tmp which
record the time and characteristics of any captured bursts.

###What to do with the data?

To make use of this valuable utilization data, the records must be processed
to create alerts or send the data to a centralized database. An existing
eAPI extension exists called simAPI. If the idea of pulling these records
from each switch over eAPI is attractive, check out the [simAPI
plugin](https://github.com/arista-eosplus/simAPI/tree/ibm).

You can also process these records and send the information to an OpenTSDB
server or create a syslog or snmp alert if certain thresholds are passed.
For help with those or any other solutions, contact the
EOS+ Consulting Services team at eosplus-dev@arista.com. 


##Installation

 If another extension with the same name is already installed, first remove that:

 **NOTE** This package was formerly called ``ibm``, but has been renamed ``burstmonitor``
```
EOS# show extensions
Name                                       Version/Release           Status extension
------------------------------------------ ------------------------- ------ ----
[ibm|burstmonitor]-<version>.rpm                 <version>/<release>        A, I   1
...
A: available | NA: not available | I: installed | NI: not installed | F: forced

EOS# no extension burstmonitor-<version>.rpm

EOS# delete extension:burstmonitor-<version>.rpm
EOS# show extensions
No extensions are available

EOS# copy installed-extensions boot-extensions
Copy completed successfully.
```

Download or clone this Github repo and run ``make rpm`` on a similar platform
as your Arista EOS device
```
admin$ make rpm
```

Copy the extension to the switch using the **copy** command:
```
EOS# copy path/to/burstmonitor-<version>.rpm extension:
```

Install the extension:
```
EOS# extension burstmonitor-<version>.rpm
```

In order to make the extension persistent over reboot, use:
```
EOS# copy installed-extensions boot-extensions
```

If everything went well, **show extensions** should show:
```
EOS#show extensions
show extensions
Name                                       Version/Release           Status extension
------------------------------------------ ------------------------- ------ ----
burstmonitor-<version>.rpm                 <version>/<release>        A, I     1

A: available | NA: not available | I: installed | NI: not installed | F: forced
```

##Configuration

####Switch configuration

The burstmonitor RPM installation will have added daemon config to your
running-config, but it's still in shutdown mode.
```
daemon burstmonitor
   exec /usr/bin/python /persist/sys/burstmonitor/burstmonitor
   shutdown
```

Before starting the **burstmonitor data collector**,
follow the steps below to modify your ``burstmonitor.json`` config file:


####BurstMonitor data collector

The data collector config file is ``/persist/sys/burstmonitor/burstmonitor.json``.
Here is an example:

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
   // default: /tmp/burstmonitor                                        
   "log_dir" : "/tmp/burstmonitor",

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
Burstmonitor will poll the hardware counters as fast as the configured by
*poll_duration* and will record the link utilization for each polling interval.
A batch of polling intervals are grouped together for reporting purposes - this
is controlled by the *batch_size* option from above. In the example from above,
every 100 consecutive polling intervals, BurstMonitor will record the
*maximum RX/TX burst* of traffic from all the polling intervals in the batch
(in CSV format).

Note that the *maximum RX/TX burst* is computed with respect to the link speed
and NOT the number of Bytes which are received/transmitted during a polling
interval. Hence, both the size (in Bytes) and length (in us) of a polling
interval are considered in order to compute the maximum burst.

Here is an example:
```
index,batch_rx_bytes,batch_tx_bytes,batch_start_ms,batch_duration_ms,burst_rx_bytes,burst_rx_perc,burst_rx_offset_ms,burst_rx_duration_ms,burst_tx_bytes,burst_tx_perc,burst_tx_offset_ms,burst_tx_duration_ms
1,2651178944,0,1.43327791883e+12,3029.877,28375296,70.041,780.039,32.41,0,0.000,0.0,30.19
...
```
The recorded data for each interface can be found in ``/tmp/burstmonitor/\<INTERFACE_NAME\>``.

For each interface, burstmonitor will store multiple log files
(named ``/tmp/burstmonitor/\<INTERFACE_NAME\>/1``,
  ``/tmp/burstmonitor/\<INTERFACE_NAME\>/2``,
  ``/tmp/burstmonitor/\<INTERFACE_NAME\>/3``, ...) and the maximum number of
  such files is configured via the *log_files* option. Each log file will
  contain up-to *log_entries* entries.

Whenever the first log file for each interface
(``/tmp/burstmonitor/\<INTERFACE_NAME\>/1``) becomes full (meaning that the
  number of recorded entries in the file equals the *log_entries* option in
  the config file), the log files for that interface are rotated as follows:

 - ``/tmp/burstmonitor/\<INTERFACE_NAME\>/1`` -> ``/tmp/burstmonitor/\<INTERFACE_NAME\>/2``
 - ``/tmp/burstmonitor/\<INTERFACE_NAME\>/2`` -> ``/tmp/burstmonitor/\<INTERFACE_NAME\>/3``
 - ...
 - ``/tmp/burstmonitor/\<INTERFACE_NAME\>/\<log_files-1\>`` -> ``/tmp/burstmonitor/\<INTERFACE_NAME\>/\<log_files\>``


Make changes to the configuration file above and then hop back into the CLI to
start the ``burstmonitor`` daemon.
```
(config)# daemon burstmonitor
(config-daemon-burstmonitor)# shutdown
(config-daemon-burstmonitor)# no shutdown

OR

(bash)# sudo pkill burstmonitor
```

To make the running-config persistent use:
```
(config)# copy running-config startup-config
```

##Output

####BurstMonitor data collector

The BurstMonitor CSV log files are stored under */tmp/burstmonitor*. Note that
the log files are cleared whenever the *burstmonitor data collector* is
restarted (either manually via the configuration of the switch, or
  automatically in case of a crash). Here is an example:

```
(bash)# cat /tmp/burstmonitor/Ethernet10/1
index,batch_rx_bytes,batch_tx_bytes,batch_start_ms,batch_duration_ms,burst_rx_bytes,burst_rx_perc,burst_rx_offset_ms,burst_rx_duration_ms,burst_tx_bytes,burst_tx_perc,burst_tx_offset_ms,burst_tx_duration_ms
1,2651178944,0,1.43327791883e+12,3029.877,28375296,70.041,780.039,32.41,0,0.000,0.0,30.19
2,2651290816,0,1.43327792186e+12,3030.005,26744640,71.324,900.061,29.998,0,0.000,0.0,31.736
3,2652512320,0,1.43327792489e+12,3031.399,26862592,71.672,2370.112,29.984,0,0.000,0.0,30.309
4,2650143360,0,1.43327792792e+12,3028.694,27566848,73.156,2848.683,30.146,0,0.000,0.0,29.512
```

##Debugging

Here are some tips for debugging BurstMonitor issues:
 - check that the extension is installed and properly configured as shown above
 - check that **BurstMonitor data collector** is running (the process name is
   *burstmonitor*). If the collector is not running, check that the daemon is
   enabled in the config (*no shutdown*):
```
(enable)# bash pgrep burstmonitor
11367
```
 - check whether **BurstMonitor data collector** is crashing and being restarted often by looking at syslog and the timestamps of */var/log/agents/burstmonitor**
 - run the **BurstMonitor data collector** manually, in debug mode:
```
(bash)$ sudo /usr/bin/python /persist/sys/burstmonitor/burstmonitor -d
sudo /usr/bin/python /persist/sys/burstmonitor/burstmonitor -d
Verifying the hardware model: DCS-7150S-52-CL
Setting process name to burstmonitor
Loading intf-to-port mapping:...
```

##Compatibility

Version 1.4.0 has been developed and tested against EOS-4.15.0F. This version
should also work on EOS versions > EOS-4.15.5F, but is not tested.
Please contact eosplus@arista.com if you would like an officially supported
release of this software.

##Limitations
The **BurstMonitor data collector** works by polling the hardware counters as
fast as possible. It will consume up to a maximum of 50% of the CPU resources.

The following configuration changes require a restart of the data collector daemon in order ensure correct behavior:
 - any changes made to the speed configuration of interfaces being monitored by the BurstMonitor (e.g. agile ports)
 - any updates of the burstmonitor extension
 - any changes made to */persist/sys/burstmonitor/burstmonitor.json*

```
(config)# daemon burstmonitor
(config-daemon-burstmonitor)# shutdown
(config-daemon-burstmonitor)# no shutdown
```

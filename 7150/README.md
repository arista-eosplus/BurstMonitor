BurstMonitor
============

The Interface Burst Monitor script monitors the maximum bit rate on an interface and generates a syslog notification whenever a burst of traffic exceeding a pre-defined threshold is detected on either the RX or TX side of the interface.

##Installation

In order to install the Interface Burst Monitor, copy 'ibm' to /mnt/flash.

Interface Burst Monitor can then be started using:

<pre>   (bash:root)# <b>python /mnt/flash/ibm [&lt;options&gt;] &lt;interface number&gt;&</b></pre>

and you can use 'nohup' utility in order to make this persistent over ssh:

<pre>   (bash:root)# <b>nohup python /mnt/flash/ibm [&lt;options&gt;] &lt;interface number&gt; &</b></pre>

See: 

<pre>   (bash:root)# <b>python /mnt/flash/ibm --help</b></pre>

for details about the command-line options.

In order to run the Interface Burst Monitor as a daemon (persistent after reboot), add the following to the startup-config:

<pre>   <b>event-handler ibm
      trigger on-boot
      action bash sudo /usr/bin/daemonize python /mnt/flash/ibm [&lt;options&gt;] &lt;interface number&gt; &
      asynchronous</b></pre>

Interface Burst Monitor process name is 'ibm-&lt;interface number&gt;', so standard Linux tools can be used to stop and restart it with different options:

<pre>   (bash:root)# <b>pkill ibm-1</b>
   (bash:root)# <b>python /mnt/flash/ibm [&lt;new-options&gt;] 1 &</b></pre>

Note that in order to make sure the Interface Burst Monitor does not restart on reboot / starts with a different config on reboot, the startup-config has to be changed accordingly.

In order to uninstall Interface Burst Monitor, use:

<pre>   (bash:root)# <b>rm /mnt/flash/ibm</b>
   (bash:root)# <b>pkill -f ibm</b></pre>

##Configuration / Debugging

Log messages are generated whenever the TX/RX maximum bit rate exceeds certain thresholds (tolerances). These tolerance levels are expressed in terms of percentage of the link speed and are by default set at 80%, for both RX and TX.  In order to change the tolerance levels, use the *--rx-tolerance/--tx-tolerance* command line options:

<pre>   (bash:root)# <b>python /mnt/flash/ibm -r 60 -t 90 &lt;interface number&gt; &</b></pre>

In order to enable debugging output to stdout, use the '-d' command line option.

<pre>   (bash:root)# <b>python /mnt/flash/ibm -d ...</b></pre>

Note that the output can be quite verbose so it is recommended that this option is used with caution, and only for debugging purposes.

##Compatibility

Version 1.1 has been developed and tested against 4.11.8. It is not officially supported. This version will also operate on >= EOS versions 4.12.6, 4.13.3, or any 4.14 release but is untested. Please contact eosplus@arista.com if you would like an officially supported release of this software.

##Limitations
The script works by polling the hardware counters ever ~1-3ms. It will consume up to a maximum of 50% of the CPU resources by default.

##Example
<pre>Oct 28 15:38:47 FRAES21 ibm-45: %INTERFACE-4-TX_BURST_DETECTED: TX burst (0.03Mb/1.829ms) detected on port 45</pre>



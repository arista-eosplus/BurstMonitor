BurstMonitor
============

The Interface Burst Monitor script monitors the maximum bit rate on an interface and generates a syslog notification whenever a burst of traffic exceeding a pre-defined threshold is detected on either the RX or TX side of the interface.

##Installation

In order to install the Interface Burst Monitor, copy 'ibm' to /mnt/flash.

Interface Burst Monitor can then be started using:

<pre>   (bash:root)# **/mnt/flash/ibm \[&lt;options&gt;\] &lt;interface number&gt;&**</pre>

and you can use 'nohup' utility in order to make this persistent over ssh:

<pre>   (bash:root)# **nohup /mnt/flash/ibm \[&lt;options&gt;\] &lt;interface number&gt; &**</pre>

See: 

<pre>   (bash:root)# **/mnt/flash/ibm --help**</pre>

for details about the command-line options.

In order to run the Interface Burst Monitor as a daemon (persistent after reboot), add the following to the startup-config:

<pre>   **event-handler ibm**
      **trigger on-boot**
      **action bash sudo /usr/bin/daemonize /mnt/flash/ibm \[&lt;options&gt;\] &lt;interface number&gt; &**
      **asynchronous**</pre>

Interface Burst Monitor process name is 'ibm-&lt;interface number&gt;', so standard Linux tools can be used to stop and restart it with different options:

<pre>   (bash:root)# **pkill ibm-1**
   (bash:root)# **/mnt/flash/ibm \[&lt;new-options&gt;\] 1 &**</pre>

Note that in order to make sure the Interface Burst Monitor does not restart on reboot / starts with a different config on reboot, the startup-config has to be changed accordingly.

In order to uninstall Interface Burst Monitor, use:

<pre>   (bash:root)# **rm /mnt/flash/ibm**
   (bash:root)# **pkill -f ibm**</pre>

##Configuration / Debugging

Log messages are generated whenever the TX/RX maximum bit rate exceeds certain thresholds (tolerances). These tolerance levels are expressed in terms of percentage of the link speed and are by default set at 80%, for both RX and TX.  In order to change the tolerance levels, use the *--rx-tolerance/--tx-tolerance* command line options:

<pre>   (bash:root)# **/mnt/flash/ibm -r 60 -t 90 &lt;interface number&gt; &**</pre>

In order to enable debugging output to stdout, use the '-d' command line option.

<pre>   (bash:root)# **/mnt/flash/ibm -d ...**</pre>

Note that the output can be quite verbose so it is recommended that this option is used with caution, and only for debugging purposes.

##Compatibility

Version 1.1 has been developed and tested against 4.11.8. Please reach out to eosplus@arista.com if you want to run this against a different EOS release.

##Limitations
The script works by polling the hardware counters ever ~1-3ms.


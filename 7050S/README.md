BurstMonitor
============

The Interface Burst Monitor script monitors the maximum bit rate on a set of interfaces and generates a syslog notification whenever a burst of traffic exceeding a pre-defined threshold is detected on either the RX or TX side of one of the interfaces.

##Installation

In order to install the Interface Burst Monitor, copy 'ibm' to /mnt/flash.

Interface Burst Monitor can then be started using:

<pre>   (bash:root)# <b>python /mnt/flash/ibm [&lt;options&gt;] &lt;interface number&gt; [&lt;interface number&gt;, &lt;interface number&gt;, ...]&</b></pre>

and you can use 'nohup' utility in order to make this persistent over ssh:

<pre>   (bash:root)# <b>nohup python /mnt/flash/ibm [&lt;options&gt;] &lt;interface number&gt; [...]&</b></pre>

See: 

<pre>   (bash:root)# <b>python /mnt/flash/ibm --help</b></pre>

for details about the command-line options.

In order to run the Interface Burst Monitor as a daemon (persistent after reboot), add the following to the startup-config:

<pre>   <b>event-handler ibm
      trigger on-boot
      action bash sudo /usr/bin/daemonize python /mnt/flash/ibm [&lt;options&gt;] &lt;interface number&gt; [...]&
      asynchronous</b></pre>

Interface Burst Monitor process name is 'ibm-&lt;interface number&gt;-&lt;interface number&gt;-...', so standard Linux tools can be used to stop and restart it with different options:

<pre>   (bash:root)# <b>pkill ibm-1</b>
   (bash:root)# <b>python /mnt/flash/ibm [&lt;new-options&gt;] 1 &</b></pre>

Note that in order to make sure the Interface Burst Monitor does not restart on reboot / starts with a different config on reboot, the startup-config has to be changed accordingly.

In order to uninstall Interface Burst Monitor, use:

<pre>   (bash:root)# <b>rm /mnt/flash/ibm</b>
   (bash:root)# <b>pkill -f ibm</b></pre>

##Configuration / Debugging

Log messages are generated whenever the TX/RX maximum bit rate exceeds certain thresholds (tolerances). These tolerance levels are expressed in terms of percentage of the link speed and are by default set at 80%, for both RX and TX.  In order to change the tolerance levels, use the *--rx-tolerance/--tx-tolerance* command line options:

<pre>   (bash:root)# <b>python /mnt/flash/ibm -r 60 -t 90 &lt;interface number&gt; &</b></pre>

The tolerance levels are configured globally and apply to all interfaces. In oder to use different thresholds for different interfaces, simply start multiple instances of the script.

In order to enable debugging output to stdout, use the '-d' command line option.

<pre>   (bash:root)# <b>python /mnt/flash/ibm -d ...</b></pre>

Note that the output can be quite verbose so it is recommended that this option is used with caution, and only for debugging purposes.

This extension works by polling the interface counters via eAPI. The eAPI credentials and protocol can be configured using the following command line options:

<pre>      # <b>python /mnt/flash/ibm --help</b>
      ...
      Options:
        ...
        -p PASSWORD, --eapi-password=PASSWORD
                              eAPI password (default="")
        -P PROTOCOL, --eapi-protocol=PROTOCOL
                              eAPI protocol (default=http)
        ...
        -u USERNAME, --eapi-username=USERNAME
                              eAPI username (default=admin)</pre>

##Compatibility

Version 1.1 has been developed and tested against 4.13.7M. Please contact eosplus@arista.com if you would like an officially supported release of this software.

##Limitations

The script works by polling the hardware counters ever ~2s. This will lead to the CPU consumption of Strata to sometimes exceed 20%.

The script only works for 10G interfaces on Arista 7050S series switches.

The script requires eAPI to be enabled.
   e.g.
<pre>     management api http-commands
       no protocol https
       protocol http
       no shutdown</pre>

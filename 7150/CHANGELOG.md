# 3.3.2 (Jun 04 2018)
* Resolves issue where burstmonitor crashes if FocalPointV2 agent state not init in sysdb.
* Fixes access failure to sysdb entity in 4.20.x releases

# 3.3.1 (Mar 17 2017)
* Add more checks to ensure FocalPointv2 is running

# 3.3.0 (Jan 27 2017)
* Fix issue where BM will restart if FocalPointv2 agent isn't started
* Add support for 25, 50, 100G interface speeds
* Fix issue where the timestamp on the record was inaccurate
* Adds startup delay of four minutes. This startup delay is only enforced when the
system uptime is less than four minutes.

# 3.2.1 (May 13 2016)
* Update lib to print the snmptrap sent

# 3.2.0 (May 12 2016)
* Add VRF support. Check burstmonitor.json for the vrf option.

# 3.1.2 (May 11 2016)
* Fix port mapping. This resolves the issue where burstmonitor crashes when it tries to gather hardware counters.

# 3.1.1 (Feb 10 2016)
* Fix snmptrap record generation

# 3.1.0 (Feb 03 2016)
* Add snmptrap trigger to BurstMonitor
* Support v2c and v3 (See changes in burstmonitor.json)

# 3.0.0 (Jan 2016)
* Update name of package to burstmonitor

# 1.0.0 (May 2015)
* Initial release

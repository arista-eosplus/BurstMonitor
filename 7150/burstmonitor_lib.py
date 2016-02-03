#!/usr/bin/env python
#
# Copyright (c) 2015, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  - Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#  - Neither the name of Arista Networks nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""The burstmonitor_lib provides common functions to help the burstmonitor
load configuration.
"""

from subprocess import call
import cjson     # pylint: disable=F0401
import re
import socket

DEFAULTS = {'snmptrap': {'enabled': 'false'},
            'interfaces': [],
            'batch_size': 100,
            'log_dir': '/tmp/burstmonitor',
            'log_files': 3,
            'log_entries': 100,
            'poll_duration': 50}

CONFIG_FILE = '/persist/sys/burstmonitor/burstmonitor.json'

# Regular expression for comments
COMMENT_RE = re.compile(
    r'(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)


def get_hostname():
    """Retrieves the linux hostname"""
    return socket.gethostname()


def load_config(debug=False):
    """Load the burstmonitor configuration file"""
    config = {}
    with open(CONFIG_FILE) as config:
        content = config.read()

        if debug:
            print 'Reading config file: %s' % content

        match = COMMENT_RE.search(content)
        while match:
            content = content[:match.start()] + content[match.end():]
            match = COMMENT_RE.search(content)

        # JSON only accepts double quotes
        content = content.replace("'", '"')
        config = cjson.decode(content)

    for key in DEFAULTS:
        if key not in config:
            config[key] = DEFAULTS[key]

    if debug:
        print 'Loading config: %s' % config

    return config


def send_trap(config, intf_data, uptime=''):
    """This method takes the configuration data found in burstmonitor.json,
    builds a valid snmptrap command and then sends it to the server.
    """
    host = get_hostname()
    intf = intf_data['name']
    trap_args = ['snmptrap']
    trap_args.append('-v')
    version = trap_args.append(config.get('version', '2c'))
    trap_args.append(version)

    if version == '2c':
        trap_args.append('-c')
        trap_args.append(config.get('community', 'public'))

    elif version == '3':
        # Send v3 snmp-inform rathern than a trap
        trap_args.append('-Ci')

        trap_args.append('-l')
        trap_args.append(config['seclevel'])
        trap_args.append('-u')
        trap_args.append(config['secname'])

        if config['seclevel'] in ['authNoPriv', 'authPriv']:
            trap_args.append('-a')
            trap_args.append(config['authprotocol'])
            trap_args.append('-A')
            trap_args.append(config['authpassword'])

        if config['seclevel'] == 'authPriv':
            trap_args.append('-x')
            trap_args.append(config['privprotocol'])
            trap_args.append('-X')
            trap_args.append(config['privpassword'])

    trap_args.append(config['snmpServer'])

    # .iso.org.dod.internet.private. .arista
    # enterprises.30065
    enterprise_oid = '.1.3.6.1.4.1.30065'
    # enterpriseSpecific = 6
    generic_trapnum = '6'
    trap_oid = '.'.join([enterprise_oid, generic_trapnum])

    trap_args.append(str(uptime))
    trap_args.append(enterprise_oid)
    trap_args.append(trap_oid)
    trap_args.append('s')

    for direction in ['tx', 'rx']:
        base_trap = trap_args
        perc = intf_data['%s_burst_perc' % direction]
        if perc >= config['threshold']:
            duration = intf_data['%s_burst_duration' % direction]
            message = ('%s, interface %s(%s): %s percent burst of traffic '
                       'observed for %sms' %
                       (host, intf, direction, perc, duration))

            base_trap.append(message)
            call(base_trap)

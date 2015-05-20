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

import optparse
import os
import re
import shutil
import subprocess
import sys

from ctypes import cdll, byref, create_string_buffer
from subprocess import PIPE

from ibm_lib import load_config
import PyClient  # pylint: disable=F0401

SPEED_TO_BITS = {
    'speedUnknown' : 10 * (2**10)**3,  # default to 10G
    'speed1Gbps' :  (2**10)**3,
    'speed10Gbps' : 10 * (2**10)**3,
    'speed40Gbps' : 40 * (2**10)**3
    }

INTF_TO_PORT = {}
PORT_TO_INTF = {}

DEBUG = False
def _trace(msg):
    if DEBUG:
        print msg

def _proc_name(name):
    _trace('Setting process name to %s' % name)
    libc = cdll.LoadLibrary('libc.so.6')
    buff = create_string_buffer(len(name) + 1)
    buff.value = name    
    libc.prctl(15, byref(buff), 0, 0, 0)

def _verify_hw_model():
    pclient = PyClient.PyClient('ar', 'Sysdb')
    fsystem = pclient.root()['ar']['Sysdb']['hardware']['entmib'].fixedSystem
    
    _trace('Verifying the hardware model: %s' %
           (fsystem and fsystem.modelName))
    
    return (fsystem and re.match('^DCS-715', 
                                 fsystem.modelName))

def _port_name(interface):
    match = re.search('^[a-zA-Z]+(.*)$', interface)
    if not match:
        assert False, 'Unrecognised interface: %s' % interface
    return 'Ethernet%s' % match.groups()[0]

def _port_mapping():
    bash_cmd = ['FastCli', '-p', '15', '-A', '-c', 
                'show platform fm6000 interface map']
    proc = subprocess.Popen(bash_cmd, stdin=PIPE, 
                            stdout=PIPE, stderr=PIPE)
    (out, _) = proc.communicate()
    for intf_mapping in out.split('\n')[3:-1]:
        intf_mapping = intf_mapping.split()

        intf_name = _port_name(intf_mapping[0]) 
        logical_port = intf_mapping[1]

        INTF_TO_PORT[intf_name] = logical_port
        PORT_TO_INTF[logical_port] = intf_name

    _trace('Loading intf-to-port mapping: %s' % INTF_TO_PORT)
    _trace('Loading port-to-intf mapping: %s' % PORT_TO_INTF)

class BurstMonitor(object):

    def __init__(self):
        self.config = load_config(DEBUG)
        self.interfaces = [_port_name(x) 
                           for x in self.config['interfaces']]

        try:
            shutil.rmtree(self.config['log_dir'])
        except OSError as err:
            if err.errno != 2: # no such file or directory
                raise err

        try:
            os.makedirs(self.config['log_dir'], 0755) 
        except OSError as err:
            if err.errno != 17: # file exists
                raise err

        self.cmd_ = ''
        self.data = {}

        # log files to rename on log rotation
        self.files_to_rename = []

        self.pc_ = PyClient.PyClient('ar', 'FocalPointV2')
        sysdb = self.pc_.root()['ar']['Sysdb']
        status = sysdb['interface']['status']['eth']['intf']
        for intf in self.interfaces:

            self.cmd_ += '''x = fm6000GetPortMibCounters(0, %s)
print x.port, x.cntRxGoodOctets, x.cntTxOctets, x.timestamp,
''' % INTF_TO_PORT[intf]

            folder = os.path.join(self.config['log_dir'], intf)

            try:
                os.makedirs(folder, 0755)
            except OSError as err:
                if err.errno != 17: # file exists
                    raise err

            log_file = os.path.join(folder, '1')

            # clear log file
            open(log_file, 'w').close()
            self.data[intf] = {
                'name' : intf,
                'folder' : folder,
                'log_file' : log_file,
                'log' : open(log_file, 'a'),
                'speed' : status[intf].speed,

                'prev_tstamp' : None,
                'prev_rx_counter' : None,
                'prev_tx_counter' : None,

                'rx_burst_start' : None,
                'rx_burst_duration' : None,
                'rx_burst' : None,
                'rx_burst_perc' : None,

                'tx_burst_start' : None,
                'tx_burst_duration' : None,
                'tx_burst' : None,
                'tx_burst_perc' : None,

                'batch_rx' : None,
                'batch_tx' : None,
                'batch_start' : None,
                'batch_duration' : None,
                }

            log_files = int(self.config['log_files'])
            for index in range(1, log_files):
                self.files_to_rename += \
                    [(os.path.join(folder, 
                                   str(log_files - index)),
                      os.path.join(folder, 
                                   str(log_files - index + 1)))]

        cmd_ = 'from FmApi import fm6000GetPortMibCounters'
        self.pc_.execute(cmd_)

        self.config['poll_index'] = 0
        self.config['data_record_index'] = 0

        while True:
            self.check_burst()

    def rotate_logs(self):
        _trace('Rotating log files')
        for source, destination in self.files_to_rename:
            try:
                if os.stat(source).st_size:
                    os.rename(source, destination)
            except OSError as err:
                if err.errno != 2: # no such file or directory
                    raise err

        for intf_data in self.data.itervalues():
            intf_data['log'] = open(intf_data['log_file'], 'a')

    def check_burst(self):
        try:
            data = self.pc_.execute(self.cmd_).split()
        except PyClient.RpcError:
            # Hardware agent restarted
            # self.pc_ = PyClient.PyClient('ar', 'FocalPointV2')
            cmd_ = 'from FmApi import fm6000GetPortMibCounters'
            self.pc_.execute(cmd_)
            data = self.pc_.execute(self.cmd_).split()            

        record_data = False
        if self.config['poll_index'] == \
                int(self.config['batch_size']):
            self.config['poll_index'] = 0
            record_data = True

            self.config['data_record_index'] += 1
            if (self.config['data_record_index'] > 
                int(self.config['log_entries'])):
                self.rotate_logs()
                self.config['data_record_index'] = 1
        else:
            self.config['poll_index'] += 1
            
        for index in range(len(data) / 4):
            start = index * 4
            self.check_intf_burst(data[start : start + 4],
                                  record_data)

    def check_intf_burst(self, input_data, record_data):

        [intf, rx_counter, tx_counter, tstamp] = input_data

        tstamp = int(tstamp)

        rx_counter = int(rx_counter)
        tx_counter = int(tx_counter)

        intf_data = self.data[PORT_TO_INTF[intf]]

        if intf_data['prev_tstamp']:
            duration = (tstamp - intf_data['prev_tstamp']) / 1000.0
            # Bytes
            rx_burst = rx_counter - intf_data['prev_rx_counter']

            # TODO: rollover
            # if rx_burst < 0:
            #     rx_burst += 2**65 * 8

            rx_percent = (rx_burst * 8 * 
                          1000 * 100) / (duration * 
                                         SPEED_TO_BITS[intf_data['speed']])
            intf_data['batch_rx'] += rx_burst

            if intf_data.get('rx_burst_perc', -1) < rx_percent:
                intf_data['rx_burst_start'] = intf_data['prev_tstamp']
                intf_data['rx_burst_duration'] = duration
                intf_data['rx_burst'] = rx_burst
                intf_data['rx_burst_perc'] = rx_percent

            # Bytes
            tx_burst = tx_counter - intf_data['prev_tx_counter']
            # TODO: rollover
            # if tx_burst < 0:
            #     tx_burst += 2**65 * 8

            tx_percent = (tx_burst * 8 *
                          1000 * 100) / (duration * 
                                         SPEED_TO_BITS[intf_data['speed']])

            intf_data['batch_tx'] += tx_burst

            if intf_data.get('tx_burst_perc', -1) < tx_percent:
                intf_data['tx_burst_start'] = intf_data['prev_tstamp']
                intf_data['tx_burst_duration'] = duration
                intf_data['tx_burst'] = tx_burst
                intf_data['tx_burst_perc'] = tx_percent

        else:
            intf_data['batch_start'] = tstamp
            intf_data['batch_rx'] = 0
            intf_data['batch_tx'] = 0
            duration = 0
            rx_burst = 0
            tx_burst = 0

        intf_data['prev_tstamp'] = tstamp
        intf_data['prev_rx_counter'] = rx_counter
        intf_data['prev_tx_counter'] = tx_counter

        if record_data:
            intf_data['batch_duration'] = (tstamp - 
                                           intf_data['batch_start']) / 1000.0
            self.record_data(intf_data)
            intf_data['batch_start'] = tstamp
            intf_data['batch_rx'] = 0
            intf_data['batch_tx'] = 0

    def record_data(self, intf_data):
        _trace('Writing log files')
        index = self.config['data_record_index']
        log = intf_data['log']
        if index == 1:
            log.write('index,'
                      'batch_rx(B),batch_tx(B),'
                      'batch_start,batch_duration(ms),'
                      'rx_burst(B),rx_burst_perc,'
                      'rx_burst_start(us),rx_burst_duration(ms),'
                      'tx_burst(B),tx_burst_perc,'
                      'tx_burst_start(us),tx_burst_duration(ms)\n')
                   
        log.write(
            '%s,'
            '%s,%s,'
            '%s,%s,'
            '%s,%.3f,'
            '%s,%s,'
            '%s,%.3f,'
            '%s,%s\n' % 
            (index,
             intf_data['batch_rx'], intf_data['batch_tx'],
             intf_data['batch_start'], intf_data['batch_duration'],
             intf_data['rx_burst'], intf_data['rx_burst_perc'],
             intf_data['rx_burst_start'], 
             intf_data['rx_burst_duration'],
             intf_data['tx_burst'], intf_data['tx_burst_perc'],
             intf_data['tx_burst_start'], 
             intf_data['tx_burst_duration']))
        log.flush()
            
def main():
    # pylint: disable=W0603

    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-d', '--debug', dest='debug', action='store_true',
                   help='print debug info')
    opts, _ = parser.parse_args()
  
    global DEBUG
    DEBUG = opts.debug

    if not _verify_hw_model():
        sys.exit('ERROR: This application only works for '
                 'Arista 7150 line of products!')

    _proc_name('ibm')
    _port_mapping()

    _ = BurstMonitor()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

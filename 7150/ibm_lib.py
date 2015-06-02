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

import cjson     # pylint: disable=F0401
import re

DEFAULTS = {'interfaces' : [],
            'batch_size' : 1000,
            'log_dir' : '/tmp/ibm',
            'log_files' : 3,
            'log_entries' : 100,
            'poll_duration' : 30}

CONFIG_FILE = '/persist/sys/ibm/ibm.json'

# Regular expression for comments
COMMENT_RE = re.compile(
    r'(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)

def load_config(debug=False):
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

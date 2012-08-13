#!/usr/bin/env python
# Copyright (C) 2012 Eric Leblond <eric@regit.org>
#
# You can copy, redistribute or modify this Program under the terms of
# the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# version 3 along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import re
from pylab import *
import numpy
import os
import sqlite3

class Counter:
    def __init__(self, name, threadname):
        self.name = name
        self.threadname = threadname
        self.values = {}
    def add_value(self, time, value):
        self.values[time] = value
    def get_value(self, time):
        try:
            return self.values[time]
        except:
            return None
    def get_values(self):
        return self.values
    def get_times(self):
        return sorted(self.values.keys())
    def merge(self, cnt):
        for time in cnt.get_times():
            if self.values.has_key(time):
                self.values[time] += int(cnt.get_value(time))
            else:
                self.values[time] = int(cnt.get_value(time))
    def derivative(self):
        deriv = Counter(self.name + "/s", self.threadname)
        prevv = 0
        i = 0
        for time in sorted(self.values.keys()):
            if i == 0:
                prev = time
            else:
                deriv.add_value(time, (float(self.get_value(time) - self.get_value(prev)))/float(time - prev))
            i += 1
        return deriv

class Stats:
    def __init__(self, runname):
        self.name = runname
        #self.counters = {}
    def load_file(self, filename):
        self.counters = {}
        logtime = ""
        reg_date = re.compile("uptime: (\d+)d, (\d+)h (\d+)m (\d+)s")
        
        for line in open(filename, 'r'):
            if "----" in line:
                continue
            elif "Date:" in line:
                 time_split = reg_date.search(line)
                 logtime = 86400 * int(time_split.group(1)) + 3600 * int(time_split.group(2)) + 60 * int(time_split.group(3)) + int(time_split.group(4))
            elif "Counter" in line:
                continue
            else: #try to parse
                (name, threadname, value) = line.split("|")
                self.add_value(name.strip(), threadname.strip(), logtime, int(value.strip()))

    def add_value(self, name, threadname, time, value):
        try:
            self.counters[name][threadname].add_value(time, value)
        #TODO exception : no key only
        except KeyError:
            if not self.counters.has_key(name):
                self.counters[name] = {}
            if not self.counters[name].has_key(threadname):
                self.counters[name][threadname] = Counter(name, threadname)
            self.counters[name][threadname].add_value(time, value)
    # TODO add way to get global counter
    def get_value(self, time, name, threadname):
        try:
            return self.counters[name][threadname].get_value(time)
        except:
            return None
    def get_values(self, name, threadname = "all"):
        return self.get_counter(name, threadname).get_values()
    def get_counter(self, name, threadname = "all"):
        if threadname == "all":
            res = Counter(name, "all")
            for key in self.counters[name].keys():
                res.merge(self.counters[name][key]) 
            return res
        else:
            return self.counters[name][threadname]

    def list_counters(self):
        return sorted(self.counters.keys())
    def list_threads(self, counter="decoder.pkts"):
        return sorted(self.counters[counter].keys())
        #try:
        #    return self.counters[name][threadname].get_values()
        #except:
        #    return None
    def plot(self, name, threadname="all", merge=True, scale=1, speed=False):
        if threadname == "all" and merge != True:
            for thname in self.counters[name].keys():
                res = self.get_counter(name, thname)
                if speed == True:
                    res = res.derivative()
                    label = thname + "/s"
                else:
                    label = thname
                res = res.get_values()
                plot(res.get_values().keys(),  numpy.multiply(scale, res.values()), '+', label=label)
        else:        
            res = self.get_counter(name, threadname)
            if speed == True:
                res = res.derivative()
                label = name + "/s"
            else:
                label = name
            res = res.get_values()
            plot(res.keys(), numpy.multiply(scale, res.values()), '+', label=label)
        legend()
    def op(self, counters_list=None, speed=False, func=min):
        if counters_list == None:
            counters_list = self.list_counters()
        res = {}
        for counter in counters_list:
            data = self.get_counter(counter)
            if speed:
                data = data.derivative()
            res[counter] = func(data.get_values().values())
        return res
    def min(self, counters_list=None, speed=False):
        return self.op(counters_list=counters_list, speed=speed, func=min)
    def max(self, counters_list=None, speed=False):
        return self.op(counters_list=counters_list, speed=speed, func=max)
    def mean(self, counters_list=None, speed=False):
        return self.op(counters_list=counters_list, speed=speed, func=mean)
    def std(self, counters_list=None, speed=False):
        return self.op(counters_list=counters_list, speed=speed, func=std)

class DBStats:
    def __init__(self, db_file):
        self.db_file = db_file
        #self.counters = {}
    def init_db(self):
        if os.path.isfile(self.db_file):
            sys.stderr.write("Will not overwrite existing file\n")
            sys.exit(1)
        conn = sqlite3.connect(self.db_file)
        conn.execute('''CREATE TABLE counters
                 (timestamp float, run_id text, host_id text, version text, counter text, min real, mean real, max real, std real)''')
        conn.commit()
        conn.close()
    def update_db(self, ST, counters_list, timestamp, run_id, host_id, version, speed=False):
        if not os.path.isfile(self.db_file):
            sys.stderr.write("'%s' is not a file\n" % (db_file))
            sys.exit(1)
        res_mean = ST.mean(counters_list, speed=speed)
        res_max = ST.max(counters_list, speed=speed)
        res_min = ST.min(counters_list, speed=speed)
        res_std = ST.std(counters_list, speed=speed)
        vcounters = []
        for key in res_mean.keys():
            vcounters.append((timestamp, run_id, host_id, version, key,
                res_min[key], res_mean[key], res_max[key], res_std[key]))
        conn = sqlite3.connect(self.db_file)
        conn.executemany("INSERT INTO counters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", vcounters)
        conn.commit()
        conn.close()

#! /usr/bin/env python
# check_emc_unisphere_disks
#
# A simple script to check the health of all disks on your emc unisphere SAN.
# v0.1 by Peter Manton

# TODO:
# Much more.. Checking storage pool space, iscsi initiators and the like...

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, sys, subprocess, re

# Global vars
uemcli_path = '/opt/emc/uemcli/bin/uemcli.sh' # Path to the unipshere CLI

try:
    unisphere_host = sys.argv[1]
    unisphere_username = sys.argv[2]
    unisphere_password = sys.argv[3]
except:
    print('Usage: check_emc_unisphere_disks <hostname/ip> <username> <password>')
    exit(3)


# Startup checks
if os.path.isfile(uemcli_path) == False:
    print('Error: It looks like you have not installed the UniSphere CLI (or it is not being pointed to the correct'
          ' path in this script - this can be downloaded from: '
          'https://support.emc.com/search?text=VNXe%20Unisphere%20CLI%20&product_id=8864&resource=DOWN&'
          '_ga=1.85856017.920998021.1461060670')
    exit(3)


# Lets check the disks...
disk_id_list = []
health_state_list = []
command = ' -d ' + unisphere_host + ' -u ' + unisphere_username + ' -p ' + unisphere_password + ' /env/disk show'
counter = 0;

p = subprocess.Popen(uemcli_path + command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT ,shell=True)
p.wait() # must wait for process to finish first!
if p.returncode != 0:
    print('Error: Unable to connect to host with username / password!')
    for line in p.stdout:
        print(line)
    exit(3)

# build array from stdout
command_result = []
for line in p.stdout:
    command_result.append(line)

# gather disk information
for line in command_result:
    # regex = r"^\d+:\s+ID\s+=\s\w{3}_(\d_\d_disk|disk)_\d+" # Full string
    regex = r"(\w{3}_(\d_\d_disk|disk)_\d+)|(DISK_\w{3}_\d+_\d+)"
    if re.search(regex, line):
        extract = re.search(regex, line)
        disk_id_list.append(extract.group(0))

# gather help state data
for line in command_result:
    # regex = r"^\d+:\s+ID\s+=\s\w{3}_(\d_\d_disk|disk)_\d+" # Full string
    regex = r"(OK|Degraded|Minor\sfailure|Major\sfailure)"
    if re.search(regex, line):
        extract = re.search(regex, line)
        health_state_list.append(extract.group(0))

# compile the lists into a dictionary
resultsDict = {};
degraded_disks = []
minor_failure_disks = []
major_failure_disks = []

for x, res in enumerate(disk_id_list):
    resultsDict[res] = health_state_list[x]

for key in resultsDict:
    if 'OK' in resultsDict[key]:
        pass
    elif 'Degraded' in resultsDict[key]:
        degraded_disks.append(key)
    elif 'Minor failure' in resultsDict[key]:
        minor_failure_disks.append(key)
    elif 'Major failure' in resultsDict[key]:
        major_failure_disks.append(key)

if len(degraded_disks) | len(minor_failure_disks) | len(major_failure_disks) < 1:
    print('OK: All ' + str(len(resultsDict)) + ' disks have no reported issues.')
    exit(0)
else:
    print('Degraded disks: ' + str(degraded_disks) + '. Minor failures: ' + str(minor_failure_disks) + '. Major failures: ' + str(major_failure_disks) + '.')
    exit(2)

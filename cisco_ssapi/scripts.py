##############################################################################
#
# Copyright (C) 2010, Chet Luther <chet.luther@gmail.com>
#
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
#
##############################################################################

import csv
import sys

from cisco_ssapi.eox import getOptionParser, Server, EOXRecord


def getEOXByDates():
    def usage(msg=None):
        if msg:
            print >> sys.stderr, msg
        print >> sys.stderr, "Usage: %s <-u username> <-p password> <-s MM/DD/YYYY> <-e MM/DD/YYYY>" % sys.argv[0]
        sys.exit(1)

    parser = getOptionParser()
    parser.add_option('-s', '--start', dest='start',
        help='Start date (MM/DD/YYYY)')
    parser.add_option('-e', '--end', dest='end',
        help='End date (MM/DD/YYYY)')
    (options, args) = parser.parse_args()

    if not options.username:
        usage("You must specify your EOX username.")

    if not options.password:
        usage("You must specify your EOX password.")

    if not options.start:
        usage("You must specify the start date.")

    if not options.end:
        usage("You must specify the end date.")

    writer = csv.writer(sys.stdout)
    writer.writerow(EOXRecord.propertyNames)

    server = Server(options.username, options.password, options.threads)

    records = server.getEOXByDates(startDate=options.start, endDate=options.end)

    for record in records:
        row = []
        for propertyName in EOXRecord.propertyNames:
            row.append(getattr(record, propertyName, ''))

        writer.writerow(row)


def getEOXBySerialNumber():
    def usage(msg=None):
        if msg:
            print >> sys.stderr, msg
        print >> sys.stderr, "Usage: %s <-u username> <-p password> <-f file> [serial] [...]" % sys.argv[0]
        sys.exit(1)

    parser = getOptionParser()
    parser.add_option('-f', '--file', dest='file',
        help='Serial number input file.')
    (options, args) = parser.parse_args()

    if not options.username:
        usage("You must specify your EOX username.")

    if not options.password:
        usage("You must specify your EOX password.")

    if not options.file and len(args) < 1:
        usage("You must specify the file option or serial number(s).")

    serials = args
    inputfile = open(options.file, 'r')
    for line in inputfile:
        serials.append(line.strip())

    writer = csv.writer(sys.stdout)
    writer.writerow(EOXRecord.propertyNames)

    server = Server(options.username, options.password, options.threads)

    records = server.getEOXBySerialNumber(serialNumbers=serials)

    for record in records:
        row = []
        for propertyName in EOXRecord.propertyNames:
            row.append(getattr(record, propertyName, ''))

        writer.writerow(row)
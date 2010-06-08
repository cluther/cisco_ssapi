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

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

import csv
import sys

from cisco_ssapi.eox import getOptionParser as eoxOptionParser
from cisco_ssapi.eox import Server, EOXException, EOXRecord


def getOptionParser():
    parser = eoxOptionParser()
    parser.add_option('-d', '--delimiter', dest='delimiter', default=',',
        help='Output field delimiter')
    return parser


def getOptions(parser, usage=None):
    options, args = parser.parse_args()

    # Enforce common required options.
    if not options.username:
        usage("You must specify your EOX username.")

    if not options.password:
        usage("You must specify your EOX password.")

    # Handle shell-escaped tab delimiter.
    if options.delimiter == '\\t':
        options.delimiter = '\t'

    return options, args


def getAllEOX():
    def usage(msg=None):
        if msg:
            print >> sys.stderr, msg
        print >> sys.stderr, "Usage: %s <-u username> <-p password>" % sys.argv[0]
        sys.exit(1)

    options = getOptions(getOptionParser(), usage)[0]

    writer = csv.writer(sys.stdout, delimiter=options.delimiter)
    writer.writerow(EOXRecord.propertyNames)

    server = Server(options.username, options.password, options.threads)

    try:
        product_ids = []
        for product in server.getAllProductIDs():
            product_ids.append(product.ProductID)
            row = []

        for record in server.getEOXByProductID(product_ids):
            for propertyName in EOXRecord.propertyNames:
                row.append(getattr(record, propertyName, ''))

            writer.writerow(row)

    except EOXException, ex:
        log.error(ex)


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
    options = getOptions(parser, usage)[0]

    if not options.start:
        usage("You must specify the start date.")

    if not options.end:
        usage("You must specify the end date.")

    writer = csv.writer(sys.stdout, delimiter=options.delimiter)
    writer.writerow(EOXRecord.propertyNames)

    server = Server(options.username, options.password, options.threads)

    try:
        records = server.getEOXByDates(
            startDate=options.start, endDate=options.end,
            chunkSize=options.chunk)

        for record in records:
            row = []
            for propertyName in EOXRecord.propertyNames:
                row.append(getattr(record, propertyName, ''))

            writer.writerow(row)

    except EOXException, ex:
        log.error(ex)


def getEOXBySerialNumber():
    def usage(msg=None):
        if msg:
            print >> sys.stderr, msg
        print >> sys.stderr, "Usage: %s <-u username> <-p password> <-f file> [serial] [...]" % sys.argv[0]
        sys.exit(1)

    parser = getOptionParser()
    parser.add_option('-f', '--file', dest='file',
        help='Serial number input file.')
    (options, args) = getOptions(parser, usage)

    if not options.file and len(args) < 1:
        usage("You must specify the file option or serial number(s).")

    serials = args
    if options.file:
        inputfile = open(options.file, 'r')
        for line in inputfile:
            serials.append(line.strip())

        inputfile.close()

    writer = csv.writer(sys.stdout, delimiter=options.delimiter)
    writer.writerow(EOXRecord.propertyNames)

    server = Server(options.username, options.password, options.threads)

    try:
        records = server.getEOXBySerialNumber(
            serialNumbers=serials, chunkSize=options.chunk)

        for record in records:
            row = []
            for propertyName in EOXRecord.propertyNames:
                row.append(getattr(record, propertyName, ''))

            writer.writerow(row)

    except EOXException, ex:
        log.error(ex)

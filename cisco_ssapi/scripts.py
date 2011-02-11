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
log = logging.getLogger('eox')

import csv
import sys
import types

from optparse import OptionParser

import eox


def getOptionParser():
    """
    Convenience method for getting an OptionParser with the common items you'll
    need to query EOX.
    """
    parser = OptionParser()
    parser.add_option('-u', '--username', dest='username',
        help='Cisco EOX username')
    parser.add_option('-p', '--password', dest='password',
        help='Cisco EOX password')
    parser.add_option('-d', '--delimiter', dest='delimiter', default=',',
        help='Output field delimiter')
    parser.add_option('-t', '--threads', dest='threads',
        type='int', default=eox.THREADS,
        help='Number of EOX server threads to use')
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


def writeProductRecords(gen, delimiter):
    writer = csv.writer(sys.stdout, delimiter=delimiter)
    writer.writerow(['ProductID', 'ProductIDDescription'])
    
    for response in gen:
        error = getattr(response, 'EOXError', None)
        if error:
            log.error('%s: %s', error.ErrorID, error.ErrorDescription)
            continue

        if not hasattr(response, 'ProductIDRecord'):
            continue
        
        for record in response.ProductIDRecord:
            error = getattr(record, 'EOXError', None)
            if error:
                log.warn('%s: %s',
                    error.ErrorID,
                    error.ErrorDescription)

            writer.writerow([record.ProductID, record.ProductIDDescription])
            sys.stdout.flush()


def writeEOXRecords(gen, delimiter):
    writer = csv.writer(sys.stdout, delimiter=delimiter)
    writer.writerow(eox.RECORD_COLUMNS)

    for response in gen:
        error = getattr(response, 'EOXError', None)
        if error:
            log.error('%s: %s', error.ErrorID, error.ErrorDescription)
            continue

        if not hasattr(response, 'EOXRecord'):
            continue

        for record in response.EOXRecord:
            error = getattr(record, 'EOXError', None)
            if error:
                log.warn('%s: %s',
                    error.ErrorID,
                    error.ErrorDescription)

                if getattr(error, 'ErrorDataType', '') == 'PRODUCT_ID': 
                    setattr(record, 'EOLProductID', error.ErrorDataValue)
                
            row = []
            for column_name in eox.RECORD_COLUMNS:
                column = getattr(record, column_name, '')
                value = None
                if column is None:
                    value = ''
                elif isinstance(column, types.StringTypes):
                    value = column
                else:
                    value = column.value
                    
                row.append(value.strip())

            writer.writerow(row)
            sys.stdout.flush()


def getAllEOX():
    def usage(msg=None):
        if msg:
            print >> sys.stderr, msg
        print >> sys.stderr, "Usage: %s <-u username> <-p password>" % sys.argv[0]
        sys.exit(1)

    options = getOptions(getOptionParser(), usage)[0]
    server = eox.Server(options.username, options.password, options.threads)
    writeEOXRecords(server.getAll(), options.delimiter)


def getAllProducts():
    def usage(msg=None):
        if msg:
            print >> sys.stderr, msg
        print >> sys.stderr, "Usage: %s <-u username> <-p password>" % sys.argv[0]
        sys.exit(1)

    options = getOptions(getOptionParser(), usage)[0]
    server = eox.Server(options.username, options.password, options.threads)
    writeProductRecords(server.getAllProductIDs(), options.delimiter)
    

def getEOXByDates():
    def usage(msg=None):
        if msg:
            print >> sys.stderr, msg
        print >> sys.stderr, "Usage: %s <-u username> <-p password> <-s MM/DD/YYYY> <-e MM/DD/YYYY>" % sys.argv[0]
        sys.exit(1)

    parser = getOptionParser()
    parser.add_option('-s', '--start', dest='start',
        help='Start date (YYYY-MM-DD)')
    parser.add_option('-e', '--end', dest='end',
        help='End date (YYYY-MM-DD)')
    options = getOptions(parser, usage)[0]

    if not options.start:
        usage("You must specify the start date (YYYY-MM-DD).")

    if not options.end:
        usage("You must specify the end date (YYYY-MM-DD.")

    server = eox.Server(options.username, options.password, options.threads)
    writeEOXRecords(
        server.getEOXByDates(options.start, options.end, None),
        options.delimiter)


def getEOXByOID():
    def usage(msg=None):
        if msg:
            print >> sys.stderr, msg
        print >> sys.stderr, "Usage: %s <-u username> <-p password> <-h hardwareType> <OID> [OID]" % sys.argv[0]
        sys.exit(1)

    parser = getOptionParser()
    parser.add_option('-h', '--hardwareType', dest='hardwareType',
        help='Hardware type')
    options, args = getOptions(parser, usage)

    if not options.hardwareType:
        usage("You must specify the hardware type.")

    if len(args) < 1:
        usage("You must specify the OID(s).")

    server = eox.Server(options.username, options.password, options.threads)
    writeEOXRecords(server.getEOXByOID(args), options.delimiter)


def getEOXByProductID():
    def usage(msg=None):
        if msg:
            print >> sys.stderr, msg
        print >> sys.stderr, "Usage: %s <-u username> <-p password> <productID> [productID] [...]" % sys.argv[0]
        sys.exit(1)

    options, args = getOptions(getOptionParser(), usage)
    if len(args) < 1:
        usage("You must specify the product ID(s).")

    server = eox.Server(options.username, options.password, options.threads)
    writeEOXRecords(server.getEOXByProductID(args), options.delimiter)


def getEOXBySWRelease():
    def usage(msg=None):
        if msg:
            print >> sys.stderr, msg
        print >> sys.stderr, "Usage: %s <-u username> <-p password> <-o osType> <swRelease> [swRelease]" % sys.argv[0]
        sys.exit(1)

    parser = getOptionParser()
    parser.add_option('-o', '--osType', dest='osType',
        help='Operating system type')
    options, args = getOptions(parser, usage)

    if not options.osType:
        usage("You must specify the operating system type.")

    if len(args) < 1:
        usage("You must specify the software release(es).")

    server = eox.Server(options.username, options.password, options.threads)
    writeEOXRecords(server.getEOXBySWReleaseString(args), options.delimiter)


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

    server = eox.Server(options.username, options.password, options.threads)
    writeEOXRecords(server.getEOXBySerialNumber(serials), options.delimiter)

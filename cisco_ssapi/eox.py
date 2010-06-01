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
log = logging.getLogger('cisco_ssapi.eox')

import re
import socket
import sys
import threading
from httplib import HTTPSConnection
from optparse import OptionParser
from xml.dom.minidom import parseString


EOX_SERVER = "wsgx.cisco.com"
EOX_URL = "/ssapi/eox/1/EOXLookupService"
EOX_URL_BULK = "/ssapi/eox/1/BulkEOXLookupService"
EOX_TIMEOUT = 60
EOX_THREADS = 4
EOX_GROUP_LIMIT = 20

SOAP_TEMPLATE = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://www.cisco.com/services/ssapi/eox/1">
<soapenv:Header/>
<soapenv:Body>
%s
</soapenv:Body>
</soapenv:Envelope>
"""


def chunkList(original, size=EOX_GROUP_LIMIT):
    """
    Conveinence method for breaking a long list into a list of lists that won't
    exceed "size" in length.
    """
    while original:
        newlist = original[:size]
        original = original[size:]
        yield newlist


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
    parser.add_option('-t', '--threads', dest='threads',
        type='int', default=4,
        help='Number of EOX server threads to use')

    return parser


class Server(object):
    def __init__(self, username, password, threads=EOX_THREADS):
        socket.setdefaulttimeout(EOX_TIMEOUT)
        self._threads = threads
        self._headers = {
            "Content-type": "text/xml; charset=utf-8",
            "User-Agent": "EOXConverter",
            "Authorization": "Basic " + ':'.join((
                username, password)).encode('base64').rstrip(),
            }


    def getAllProductIDs(self):
        action = 'showAllProductIDs'
        method = 'ShowAllProductIDsRequest'
        body = ''

        count = 0
        for ns, xml in self.getPaginatedResults(action, method, body):
            for eoxRecord in xml.getElementsByTagName('%s:ProductIDRecord' % ns):
                count += 1
                yield ProductIDRecord(ns, eoxRecord)

        log.info("Retrieved %s records from %s method.", count, method)


    def getEOXByDates(self, startDate, endDate, eoxAttrib=None):
        action = 'showEOXByDates'
        method = 'ShowEOXByDatesRequest'

        extra = None
        if eoxAttrib:
            extra = '<ns:eoxAttrib>%s</ns:eoxAttrib>' % eoxAttrib
        else:
            extra = ''

        body = """
            <ns:startDate>%s</ns:startDate>
            <ns:endDate>%s</ns:endDate>
            %s
            """ % (startDate, endDate, extra)

        count = 0
        for ns, xml in self.getPaginatedResults(action, method, body):
            for eoxRecord in xml.getElementsByTagName('%s:EOXRecord' % ns):
                count += 1
                yield EOXRecord(ns, eoxRecord)

        log.info("Retrieved %s records from %s method.", count, method)


    def getEOXByOID(self, oids, hardwareType=None):
        action = 'showEOXByOID'
        method = 'ShowEOXByOIDRequest'

        extra = None
        if hardwareType:
            extra = '<ns:HardwareType>%s</ns:HardwareType>' % hardwareType
        else:
            extra = ''

        for chunk in chunkList(oids):
            body = ''
            for oid in chunk:
                body += '<ns:OIDRecord><ns:OID>%s</ns:OID>%s</ns:OIDRecord>' % (
                    oid, extra)

            for eoxRecord in self.getResults(action, method, body):
                yield eoxRecord


    def getEOXByProductID(self, productIDs):
        action = 'showEOXByProductID'
        method = 'ShowEOXByProductIDRequest'

        for chunk in chunkList(productIDs):
            body = """
                <ns:ProductIDs>%s</ns:ProductIDs>
                """ % ','.join(chunk)

            for eoxRecord in self.getResults(action, method, body):
                yield eoxRecord


    def getEOXBySerialNumber(self, serialNumbers):
        action = 'showEOXBySerialNumber'
        method = 'ShowEOXBySerialNumberRequest'

        for chunk in chunkList(serialNumbers):
            body = """
                <ns:SerialNumbers>%s</ns:SerialNumbers>
                """ % ','.join(chunk)

            for eoxRecord in self.getResults(action, method, body):
                yield eoxRecord


    def getEOXBySWReleaseString(self, swReleaseStrings, osType=None):
        action = 'showEOXBySWReleaseString'
        method = 'ShowEOXBySWReleaseStringRequest'

        extra = None
        if osType:
            extra = '<ns:OSType>%s</ns:OSType>' % osType
        else:
            extra = ''

        for chunk in chunkList(swReleaseStrings):
            body = ''
            for swReleaseString in chunk:
                body += '<ns:SWReleaseStringRecord><ns:SWReleaseString>%s</ns:SWReleaseString>%s</ns:SWReleaseStringRecord>' % (
                    swReleaseString, extra)

            for eoxRecord in self.getResults(action, method, body):
                yield eoxRecord


    def getResults(self, action, method, body):
        log.info("Calling %s method.", method)
        body = """
            <ns:%s>
            %s
            </ns:%s>
            """ % (method, body, method)

        ns, xml = self.soapCall(action, method, body, bulk=False)

        count = 0
        for eoxRecord in xml.getElementsByTagName('%s:EOXRecord' % ns):
            count += 1
            yield EOXRecord(ns, eoxRecord)

        log.info("Retrieved %s records from %s method.", count, method)


    def getPaginatedResults(self, action, method, body, page=1):
        log.info("Calling %s method: page %s.", method, page)
        local_body = """
            <ns:%s>
            %s
            <ns:PaginationRequestRecord>
                <ns:PageIndex>%s</ns:PageIndex>
            </ns:PaginationRequestRecord>
            </ns:%s>
            """ % (method, body, page, method)

        ns, xml = self.soapCall(action, method, local_body, bulk=True)
        lastIndex = int(xml.getElementsByTagName(
            '%s:LastIndex' % ns)[0].childNodes[0].data)

        yield (ns, xml)

        if page == 1:
            log.info("%s pages available for %s.", lastIndex, method)
            page += 1
            threads = {}
            while True:
                for key, thread in threads.items():
                    if not thread.isAlive():
                        ns, xml = thread.getResults()
                        yield (ns, xml)
                        del(threads[key])

                if len(threads.keys()) == 0 and page >= lastIndex:
                    break

                while page <= lastIndex and len(threads.keys()) < self._threads:
                    thread = PagingThread(self, action, method, body, page)
                    page += 1
                    threads[page] = thread
                    thread.start()


    def soapCall(self, action, method, body, bulk=False):
        headers = self._headers
        headers.update({'SOAPAction': action})
        body = SOAP_TEMPLATE % body

        xml_string = None
        for i in range(10):
            try:
                conn = HTTPSConnection(EOX_SERVER, 443)
                conn.request(
                    "POST", bulk and EOX_URL_BULK or EOX_URL, body, headers)
                response = conn.getresponse()
                xml_string = response.read()
            except socket.timeout:
                continue

            # The XMLNS keeps changing. Figure it out dynamically.
            match = re.search(r' xmlns:(axis[^=]+)', xml_string)
            if match:
                return (match.group(1), parseString(xml_string))

        raise Exception("Persistent EOX Server Errors")


class PagingThread(threading.Thread):
    def __init__(self, eox, action, method, body, page):
        self._eox = eox
        self._action = action
        self._method = method
        self._body = body
        self._page = page
        threading.Thread.__init__(self)

    def run(self):
        results = self._eox.getPaginatedResults(
            self._action, self._method, self._body, self._page)
        for ns, xml in results:
            self._ns, self._xml = ns, xml

    def getResults(self):
        return (self._ns, self._xml)


class EOXType(object):
    propertyNames = tuple()

    def __init__(self, ns, element):
        for propertyName in self.propertyNames:
            try:
                value = element.getElementsByTagName(
                    '%s:%s' % (ns, propertyName))[0].childNodes[0].data
            except IndexError:
                value = None

            setattr(self, propertyName, value)

    def __str__(self):
        return '\n'.join(['%s=%s' % (x, y) for x, y in self.__dict__.items()])


class EOXError(EOXType):
    propertyNames = (
        'ErrorID',
        'ErrorDescription',
        )


class EOXRecord(EOXType):
    propertyNames = (
        'EOLProductID',
        'ProductIDDescription',
        'ProductBulletinNumber',
        'LinkToProductBulletinURL',
        'EOXExternalAnnouncementDate',
        'EndOfSaleDate',
        'EndOfSWMaintenanceReleases',
        'EndOfRoutineFailureAnalysisDate',
        'EndOfServiceContractRenewal',
        'LastDateOfSupport',
        'EndOfSvcAttachDate',
        'UpdatedTimeStamp',
        'EOXInputType',
        'EOXInputValue',
        )

    def __init__(self, ns, eoxRecord):
        try:
            self.EOXError = EOXError(
                ns, eoxRecord.getElementsByTagName('%s:%s' % (
                    ns, 'EOXError'))[0])
        except IndexError:
            self.EOXError = None

        try:
            self.EOXMigrationDetails = EOXMigrationDetails(
                ns, eoxRecord.getElementsByTagName('%s:%s' % (
                    ns, 'EOXMigrationDetails'))[0])
        except IndexError:
            self.EOXMigrationDetails = None

        super(EOXRecord, self).__init__(ns, eoxRecord)


class EOXMigrationDetails(EOXType):
    propertyNames = (
        'PIDActiveFlag',
        'MigrationInformation',
        'MigrationOption',
        'MigrationProductId',
        'MigrationProductName',
        'MigrationStategy',
        'MigrationProductInfoURL',
        )


class ProductIDRecord(EOXType):
    propertyNames = (
        'ProductID',
        'ProductIDDescription',
        )


# if __name__ == '__main__':
#     eox = EOX('username', 'password')
#     results = eox.getAllProductIDs()
#     results = eox.getEOXByDates(startDate='01/01/2009', endDate='12/31/2010')
#     results = eox.getEOXByOID(oids=['.1.3.6.1.4.1.9.1.18'], hardwareType='Chassis')
#     results = eox.getEOXByProductID(productIDs=['AIM-VPN/EP', 'AIM-VPN/EPII'])
#     results = eox.getEOXBySerialNumber(serialNumbers=['CAM08122874', 'FDO1351SGL9', 'AZBW7030113'])
#     results = eox.getEOXBySWReleaseString(swReleaseStrings=['9.21(7)'], osType='IOS')
#     for record in results:
#         print record
#         print "-------------------------------------------------------------"
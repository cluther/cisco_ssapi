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

import threading
import types

from suds.client import Client, WebFault

WSDL = "http://www.cisco.com/web/tsweb/ssapi/v1/downloads/eoxlookupservice-1.xml"
WSDL_BULK = "http://www.cisco.com/web/tsweb/ssapi/v1/downloads/bulkeoxlookupservice-1.xml"
THREADS = 4
GROUP_LIMIT = 20

RECORD_COLUMNS = [
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
    ]


class Server(object):
    bulkMethods = ['showAllProductIDs', 'showEOXByDates']

    def __init__(self, username, password, threads=THREADS):
        self._username = username
        self._password = password
        self._threads = threads


    def getAll(self):
        for response in self.getAllProductIDs():
            product_ids = []
            for record in response.ProductIDRecord:
                product_ids.append(record.ProductID)

            for record in self.getEOXByProductID(product_ids):
                yield record


    def getAllProductIDs(self):
        for product in self.getResponses('showAllProductIDs', []):
            yield product


    def getEOXByDates(self, startDate, endDate, eoxAttrib=None):
        gen = self.getResponses('showEOXByDates',
            [startDate, endDate, eoxAttrib])

        for record in gen:
            yield record        


    def getEOXByOID(self, oids, hardwareType=None):
        method = 'showEOXByOID'
        client = self.getClient(method)

        oid_records = []
        for oid in oids:
            record = client.factory.create('OIDType')
            record.OID = oid
            record.HardwareType = hardwareType
            oid_records.append(record)
        
        for record in self.getResponses(method, [oid_records]):
            yield record


    def getEOXByProductID(self, productIDs):
        for record in self.getResponses('showEOXByProductID', [productIDs]):
            yield record


    def getEOXBySWReleaseString(self, swReleaseStrings, osType=None):
        method = 'showEOXBySWReleseString'
        client = self.getClient(method)
        
        swReleaseString_records = []
        for swReleaseString in swReleaseStrings:
            record = client.factory.create('SWReleaseStringType')
            record.SWReleaseString = swReleaseString
            record.OSType = osType
            swReleaseString_records.append(record)

        for record in self.getResponses(method, [swReleaseString_records]):
            yield record


    def getEOXBySerialNumber(self, serialNumbers):
        gen = self.getResponses('showEOXBySerialNumber', [serialNumbers])
        for record in gen:
            yield record


    def getClient(self, method):
        wsdl = None
        if method in self.bulkMethods:
            wsdl = WSDL_BULK
        else:
            wsdl = WSDL

        return Client(wsdl, username=self._username, password=self._password)


    def getResponses(self, method, args):
        if method in self.bulkMethods:
            return self.getPaginatedResponses(method, args)
        else:
            return self.getChunkedResponses(method, args)


    def getPaginatedResponses(self, method, args):
        client = self.getClient(method)

        first_thread = PagingThread(client, method, args, 1)
        first_thread.start()
        first_thread.join()
        first_response = first_thread.getResponse()
        if not first_response:
            return
    
        yield first_response
    
        pager = getattr(first_response, 'PaginationResponseRecord', None)
        if not pager:
            return
        
        total_pages = pager.LastIndex
        next_page = 2
    
        threads = {}
        while True:
            for key, thread in threads.items():
                if not thread.isAlive():
                    response = thread.getResponse()
                    yield response
                    del(threads[key])
    
            if len(threads.keys()) == 0 and next_page > total_pages:
                break
    
            while next_page <= total_pages \
                and len(threads.keys()) < self._threads:

                thread = PagingThread(client, method, args, next_page)
                threads[next_page] = thread
                next_page += 1
                thread.start()


    def getChunkedResponses(self, method, args):
        chunked_args = chunkList(args[0])
        total_chunks = len(chunked_args)
        next_chunk = 1

        threads = {}
        while True:
            for key, thread in threads.items():
                if not thread.isAlive():
                    responses = thread.getResponses()
                    for response in responses:
                        yield response
                    del(threads[key])

            if len(threads.keys()) == 0 and next_chunk > total_chunks:
                break
    
            while next_chunk <= total_chunks \
                and len(threads.keys()) < self._threads:

                parsed_args = chunked_args[next_chunk-1]
                if isinstance(parsed_args[0], types.StringTypes):
                    parsed_args = ','.join(parsed_args)

                thread = ChunkingThread(self, method, [parsed_args], next_chunk)
                threads[next_chunk] = thread
                next_chunk += 1
                thread.start()


class PagingThread(threading.Thread):
    def __init__(self, client, method, args, page):
        self._client = client
        self._method = method
        self._args = args
        self._page = page
        self._response = None
        threading.Thread.__init__(self)
        self.name = "page %s" % self._page


    def run(self):
        pr = self._client.factory.create('PaginationRequestRecordType')
        pr.PageIndex = self._page
        args = self._args + [pr]
        log.info('requesting page %s', self._page)

        while True:
            try:
                # pylint: disable-msg=W0142
                self._response = getattr(
                    self._client.service, self._method)(*args)
                break
            except WebFault, ex:
                fault = getattr(ex, 'fault', None)
                if fault and fault.faultstring == 'Timeout':
                    log.warn('timeout requesting page %s, retrying', self._page)
                    continue

                raise ex

        pager = getattr(
            self._response, 'PaginationResponseRecord', None)

        if pager:
            log.info('received %s of %s records on page %s of %s',
                pager.PageRecords,
                pager.TotalRecords,
                pager.PageIndex,
                pager.LastIndex)


    def getResponse(self):
        return self._response


class ChunkingThread(threading.Thread):
    def __init__(self, server, method, args, chunk):
        self._server = server
        self._method = method
        self._args = args
        self._chunk = chunk
        self._responses = []
        threading.Thread.__init__(self)
        self.name = "chunk %s" % self._chunk


    def run(self):
        log.info('requesting chunk %s', self._chunk)
        response_gen = self._server.getPaginatedResponses(
            self._method, self._args)

        for response in response_gen:
            self._responses.append(response)

        log.info('received chunk %s', self._chunk)


    def getResponses(self):
        return self._responses


def chunkList(original, size=GROUP_LIMIT):
    chunked_lists = []
    while original:
        newlist = original[:size]
        original = original[size:]
        chunked_lists.append(newlist)

    return chunked_lists

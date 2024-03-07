import json
import requests
import os
import base64
import zlib
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from lxml import etree as ET
from timeit import default_timer as timer

env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

with open(env_file) as file:
    env = json.loads(file.read())

class Star:

    STAR_URL = env['STAR_URL']
    HEADERS_GETDEVICES = {
        'content-type': 'text/xml',
        'User-Agent': env['STAR_USER_AGENT']
    }

    HEADERS_GET_TEST_CASE_RESULT2 = {
            'content-type': 'text/xml; charset=utf-8',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; MS Web Services Client Protocol 4.0.30319.42000)',
            'SOAPAction': env['SOAP_ACTION']
        }
    SID = env['SID']


    @classmethod
    def get_projects(cls) -> list:
        """Returns list that contains names and updated time for all projects"""

        soap_request_body = f'<?xml version="1.0" encoding="utf-8"?>\
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"\
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema">\
                        <soap:Body><GetDevices_AVT xmlns="http://tempuri.org/">\
                            <oper>TMO</oper>\
                                <sid>{cls.SID}</sid>\
                                    </GetDevices_AVT>\
                                        </soap:Body>\
                                            </soap:Envelope>'

        response = requests.post(cls.STAR_URL,
                                 data=soap_request_body,
                                 headers=cls.HEADERS_GETDEVICES)


        xml_parser = ET.XMLParser(recover=True, ns_clean=True, remove_blank_text=True)
        etree_projects = ET.fromstring(response.content, parser=xml_parser)

        tables_of_projects = etree_projects.xpath('//Table')
        
        projetcs_list = []

        for table in tables_of_projects:
            project = {}
            for el in table:
                if el.tag == 'Name':
                    project[el.tag] = el.text
                elif el.tag == 'Last_x0020_Update':
                    project[el.tag] = parse_datetime(el.text)  - timedelta(hours=6)

            projetcs_list.append(project)
        
        return projetcs_list
    
    @classmethod
    def get_device_project(cls, device_model: str) -> bytes:
        """Returns a whole project for requested device"""

        timer_start = timer()
        soap_request_body = f'<?xml version="1.0" encoding="utf-8"?> \
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" \
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">\
                <soap:Body>\
                    <GetTestCaseResults2_AVT xmlns="http://tempuri.org/">\
                        <model>{device_model}</model>\
                        <checkListName/><priority/>\
                        <sid>{cls.SID}</sid>\
                    </GetTestCaseResults2_AVT>\
                </soap:Body>\
            </soap:Envelope>'

        response = requests.post(cls.STAR_URL,
                                 data=soap_request_body,
                                 headers=cls.HEADERS_GET_TEST_CASE_RESULT2)

        seconds = timer() - timer_start
        print(f'The project {device_model} has been downloaded in {int(seconds)} seconds.')
        timer_start = timer()

        return response.content

    def __decompress_gzip_string(compressed_data: str) -> str:
        """Decompresses a gzip string"""

        decompressed_string = zlib.decompress(
            base64.b64decode(compressed_data),
            16 + zlib.MAX_WBITS).decode('utf-8')

        return decompressed_string
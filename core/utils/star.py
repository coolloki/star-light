import json
import requests
import os
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from lxml import etree as ET

env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

with open(env_file) as file:
    env = json.loads(file.read())

class Star:

    STAR_URL = env['STAR_URL']
    HEADERS_GETDEVICES = {
        'content-type': 'text/xml',
        'User-Agent': env['STAR_USER_AGENT']
    }
    SID = env['SID']


    @classmethod
    def get_projects(cls) -> list:
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
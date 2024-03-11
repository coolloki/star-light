import json
import requests
import os
import base64
import zlib
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from lxml import etree
from timeit import default_timer as timer
from core.models import Category


env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

with open(env_file) as file:
    env = json.loads(file.read())

def parse_xml(xml) -> etree._Element:
    """Parses xml to etree element"""

    xml_parser = etree.XMLParser(recover=True, ns_clean=True, remove_blank_text=True)
    project_etree_elm = etree.fromstring(xml, parser=xml_parser)
    return project_etree_elm

def decompress_gzip_string(compressed_data: str) -> str:
    """Decompresses a gzip string"""

    decompressed_string = zlib.decompress(
        base64.b64decode(compressed_data),
        16 + zlib.MAX_WBITS).decode('utf-8')

    return decompressed_string

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
    ALL_ACTIVE_CATEGORIES = list(Category.objects.filter(is_active=True).values('id', 'title'))

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

        etree_projects = parse_xml(response.content)
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

        download_time = "{:.2f}".format(timer() - timer_start)

        print(f'The project {device_model} has been downloaded in {download_time} seconds.')

        return response.content

class Project:

    NECESSARY_TC_ITEMS = (
            'displayorder',
            'TestDescription',
            'TestCriteria',
            'TestCaseName',
            'CategoryName',
            'Priority',
            'usku_v2',
            'usku_v3',
            'mr_usku_v2',
            'mr_usku_v3',
            'tc911',
            'CustomerComments',
            'TPComment',
            'MELDefectType',
            'IsStep')

    def __init__(self, device_model, filters={}):
        
        star_instance = Star()
        raw_project = star_instance.get_device_project(device_model)
        timer_start = timer()

        if 'categories' in filters:
            categories = [dict['title'] for dict in star_instance.ALL_ACTIVE_CATEGORIES if str(
                dict['id']) in filters['categories']]
        else:
            categories = [dict['title'] for dict in star_instance.ALL_ACTIVE_CATEGORIES]

        self.project_etree = parse_xml(raw_project)

        self.list_of_binaries = self.__get_list_of_binaries(self.project_etree)
        self.current_binary_version = self.list_of_binaries[-1]
        self.previous_biniry_version = self.list_of_binaries[-2]
        self.__remove_testcases_which_not_belong_to_categories(self.project_etree, categories)
        raw_list_of_tc = self.__get_raw_list_of_test_case(self.project_etree, filters={})
       
        list_of_tc = []
        testcase_int_id = 1

        for tc in raw_list_of_tc:

            test_case = {}
            for el in tc:
                if el.tag == self.current_binary_version:
                    test_case['LastVersionResult'] = el.text
                elif el.tag == self.previous_biniry_version:
                    test_case['PreviousVersionResult'] = el.text
                if el.tag in self.NECESSARY_TC_ITEMS and el.text != None:
                    test_case[el.tag] = el.text
            test_case['incude'] = True

            if filters['Priority'] == 'P0' and test_case['Priority'] != 'P0':
                test_case['incude'] = False
            elif filters['Priority'] == 'P1' and test_case['Priority'] not in ('P0', 'P1'):
                test_case['incude'] = False
            elif filters['Priority'] == 'P2' and test_case['Priority'] not in ('P0', 'P1', 'P2'):
                test_case['incude'] = False

            if 'Variant' in filters and filters['Variant'] not in test_case:
                test_case['incude'] = False

            if 'tc911' not in filters and 'tc911' in test_case:
                test_case['incude'] = False

            if test_case.get('LastVersionResult') in ('Fail', 'NS', 'Block', 'NT') \
                and 'CustomerComments' not in test_case:
                test_case['issue'] = 'Missing Comment'
            elif test_case.get('LastVersionResult') == 'Fail' and 'MELDefectType' not in test_case:
                test_case['issue'] = 'Missing DefectType'

            elif 'only_blank' in filters and 'LastVersionResult' in test_case and 'issue' not in test_case:
                test_case['incude'] = False

            if test_case['incude'] == True:
                test_case['testcase_int_id'] = 'testcase_int_id-' + \
                    str(testcase_int_id)
                testcase_int_id += 1
                list_of_tc.append(test_case)

        sorted_list_by_tc = sorted(
            list_of_tc, key=lambda d: d['displayorder'])


        self.sorted_list_of_tc_by_category = sorted(
            sorted_list_by_tc, key=lambda d: d['CategoryName'])

        
        # parse_time = timer() - timer_start
        self.parse_time = "{:.2f}".format(timer() - timer_start)

        print(f'The response for {device_model} has been parsed and data has been processed in {self.parse_time} seconds.')

        print('_' * 15)

 
    @classmethod
    def __get_list_of_binaries(cls, project_etree: etree._Element) -> list:
        """Returns list of projects binaries versions"""

        namespace = {"xs": "http://www.w3.org/2001/XMLSchema"}
        head_of_table = project_etree.xpath('(//xs:sequence)[1]/xs:element', namespaces=namespace)

        list_of_binaries_versions = []
        for el in head_of_table:
            if el.attrib.get('name') not in ('mtp', 'PTN', 'sdf') and \
                len(el.attrib.get('name')) == 3:
                    list_of_binaries_versions.append(el.attrib.get('name'))
        return list_of_binaries_versions
    
    @classmethod
    def __remove_testcases_which_not_belong_to_categories(cls, project_etree: etree._Element, categories: list):
        test_groups = project_etree.xpath('//CategoryName')
        for group in test_groups:
            if group.text not in categories:
                group.getparent().getparent().remove(group.getparent())

    @classmethod
    def __get_raw_list_of_test_case(cls, project_etree: etree._Element, filters={}) -> list:
        """Returns list of etree element with test cases"""

        namespace = {"diffgr": "urn:schemas-microsoft-com:xml-diffgram-v1"}
        if 'only_blank' in filters:
            list_of_tc = project_etree.xpath(f'//TestCaseResults2[@diffgr:hasChanges="modified" and ( not(descendant::{cls.current_binary_version}) or (descendant::{cls.current_binary_version} and descendant::{cls.current_binary_version}[text()]) )]', namespaces=namespace)
        else:
            list_of_tc = project_etree.xpath('//TestCaseResults2[@diffgr:hasChanges="modified"]', namespaces=namespace)
        
        return list_of_tc

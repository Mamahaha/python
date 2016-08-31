#!/usr/bin/python
#-*-coding:utf-8 -*-
'''
Created on Aug 26, 2016

@author: led
'''

import xml.etree.ElementTree as ET
import xml.sax



MODULE_FOLDER = '/home/led/gh/python/record'
module_list = []

class RecordHandler(xml.sax.ContentHandler):
    '''
    Deprecated. 
    Cause: Cannot get the value of multi-line string
    '''
    def __init__(self):
        self.CurrentData = ''
        self.name = ''
        self.version = ''
        self.description = ''
        self.value = ''
    
    def startElement(self, tag, attribute):
        self.CurrentData = tag
        if tag == 'feature':
            print '****Feature****'
    
    def endElement(self, tag):
        if self.CurrentData == 'name':
            print 'Name: ', self.name
        elif self.CurrentData == 'version':
            print 'Version:', self.version
        elif self.CurrentData == 'description':
            print 'Description:', self.description
        elif self.CurrentData == 'content':
            print 'Content:', self.value
        #else:
        #    print 'Error: Tag <%s> not supported' %(self.CurrentData)
        self.CurrentData = ''

    def characters(self, content):
        if self.CurrentData == 'name':
            self.name = content
        elif self.CurrentData == 'version':
            self.version = content
        elif self.CurrentData == 'description':
            self.description = content
        elif self.CurrentData == 'content':
            self.value = content
        #else:
        #    print 'Error: Value <%s> not supported' %(content)
 
def test_RecordHandler(file_path):
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    
    handler = RecordHandler()
    parser.setContentHandler(handler)
    parser.parse(file_path)           


def test_ET(file_path):
    '''
    Preferred
    '''
    tree = ET.ElementTree(file='/tmp/bmc.xml')
    root = tree.getroot()
    names = root.findall('./feature/content')
    for name in names:
        print name.text

import sys
def log_error_and_exit(msg):
    printc('black', 'red', 'ERROR: %s\n' %msg)
    sys.exit()

import os
def init():
    global module_list
    for root, dirs, files in os.walk('%s/data' %(MODULE_FOLDER)):
        module_list = files

def get_module(m_prefix):
    init()
    tmp_prefix =  m_prefix.strip().lower()
    target_modules = [i for i in module_list if i.startswith(tmp_prefix)]

    if len(target_modules) == 0:
        log_error_and_exit('No such component: %s' %m_prefix)
    
    if len(target_modules) > 1:
        log_error_and_exit('More than one module has the prefix: <%s>. Please input a more accurate module name' %m_prefix)
    return target_modules[0]

def list_module():
    for file_name in module_list:
        printc('black', 'yellow', '* %s' %(file_name.split('.')[0]))
    print ''
   
def list_feature(m_prefix):
    target_module = get_module(m_prefix)
        
    tree = ET.ElementTree(file='%s/data/%s' %(MODULE_FOLDER, target_module))
    root = tree.getroot()
    features = root.findall('./feature')
    #print '===============Feature list in %s================' %(module_name)
    for feature in features:
        if feature.attrib['name'] != '':
            #print '  * %s' %(feature.attrib['name'])
            ver = feature.attrib['version']
            des = feature.find('description').text
            if ver == None or ver == '':
                ver = 'common'
            if des == None or des == '':
                des = 'N/A'
            line = '* ' + feature.attrib['name'].ljust(20) + ' | ' + ver.ljust(7) + ' | ' + des
            printc('black', 'yellow', line)
    print ''   
    

def show_feature(module_name, feature_name):
    target_module = get_module(module_name)
       
    tree = ET.ElementTree(file='%s/data/%s' %(MODULE_FOLDER, target_module))
    root = tree.getroot()
    features = root.findall('./feature')
    for feature in features:
        if feature.attrib['name'].startswith(feature_name.strip().lower()):
            printc('blue', 'white', '===============%s================' %(feature.attrib['name']))
            #print '  * Description:', feature.find('description').text
            #print '  * Content:'
            if feature.attrib.has_key('type'):
                show_content(feature.find('content').text, feature.attrib['type'])
            else:
                show_content(feature.find('content').text, 'text')

def show_content(content, content_type):
    if content_type == 'code':
        lines = content.split('\n')    
        for line in lines:
            printc('black', 'green', '%s' %(line))
    elif content_type == 'text':
        lines = content.strip().split('\n')
        for line in lines:
            ll = line.strip()
            if ll.startswith('----'):
                printc('black', 'yellow', '%s' %(ll))
            else:
                printc('black', 'green', '%s' %(ll))

        print ''


#===============colorful output=========
fgc_dict = {
            'red' : 31,
            'green' : 32,
            'yellow' : 33,
            'blue' : 34,
            'purple' : 35,
            'deep_g' : 36,
            'white' : 37,
            'black' : 30
            }

bgc_dict = {
            'red' : 41,
            'green' : 42,
            'yellow' : 43,
            'blue' : 44,
            'purple' : 45,
            'white' : 47,
            'black' : 49
            }

def printc(bgc,fgc, msg):
    print '\033[%d;%dm%s\033[0m' %(bgc_dict[bgc], fgc_dict[fgc], msg)


st = [{"name":"promote","version":"common","type":"text","description":"N/A","content":"\n      \"cp\"  : /opt/twiddle/bin/twiddle.sh -s service:jmx:remoting-jmx://127.0.0.1:9999 invoke com.ericsson.bmsc.mdfcp:service=MdfcpFailoverService promote\n      \"up\"  : pkill -39 mdf-up\n      \"adf\" : /opt/twiddle/bin/twiddle.sh -s service:jmx:remoting-jmx://127.0.0.1:9999 invoke com.ericsson.bmsc.adf.provisioning.failover:service=AdfProvisioningFailoverService promote\n    "}
,{"name":"license","version":"common","type":"text","description":"Licenses are installed on 2 MDF-DB and ADF-DB nodes","content":"\n      -----------------install a license-----------------\n      su - sentinel\n\t\t\t/opt/sentinel/default/bin/lslic -F /tmp/[license_file_name]\n\t\t\t/opt/sentinel/default/bin/lsmon\n\t\t\t\n\t\t\t-----------------remove a license-----------------\n\t\t\t/opt/sentinel/default/bin/lslic -DL [feature_name] [feature_version] [license_hash_of_inactive_license]\n    "} 
, {"name":"mdfdb","version":"15a","type":"text","description":"Access Oracle","content":"\n      -----------------Log on to Oracle-----------------\n      # su - oracle\n\t\t\t$ sqlplus 'bmsc/eMbMs1234!'\n\t\t\tSQL> select table_name from user_tables;\n\t\t\tSQL> desc T_DELIVERY_SESSION_INSTANCE;\n\t\t\t-----------------Clear all sessions in mdf-db-----------------\n\t\t\tdelete from t_bmsc_event;\n\t\t\tdelete from t_content;\n\t\t\tdelete from t_delivery_content;\n\t\t\tdelete from t_delivery_session;\n\t\t\tdelete from t_delivery_session_instance;\n\t\t\tdelete from t_embms_session;\n\t\t\tdelete from t_fec_info;\n\t\t\tdelete from t_gateway_info;\n\t\t\tdelete from t_file_repair;\n\t\t\tdelete from t_qos_metrics;\n\t\t\tdelete from t_reception_report;\n\t\t\tdelete from t_success_report;\n\n\t\t\tcommit;\n    "}]

if __name__ != '__main__':
    init()
    if len(sys.argv) == 1:
        list_module()
    elif len(sys.argv) == 2:
        list_feature(sys.argv[1])
    elif len(sys.argv) == 3: 
        show_feature(sys.argv[1], sys.argv[2])
    else:
        log_error_and_exit('Input parameters are limited to 2') 
else:
    import json
    b = json.dumps(st, indent=1)
    print b
    
    
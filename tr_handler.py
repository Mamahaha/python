#!/usr/bin/env python


import getpass    
import requests
import json
import time
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from HTMLParser import HTMLParser
from lxml import html



###############################################################################################################
#                           History functions
###############################################################################################################
def parse_single(tr_num):
    try:
        url = 'https://mhweb.ericsson.se/TREditWeb/faces/oo/object.xhtml?eriref=%s' %(tr_num)
        resp = http_get(url)
        tree = html.fromstring(resp.text.encode('utf-8'))

        #print tr_num
        status_phase = tree.xpath('//div[@class="rf-cp-lbl-exp"]//span[@class="headingLabelValue"]/text()')[0].strip()
        print 'status_phase: '.ljust(20), status_phase
        if status_phase in ['Finished/Archive', 'Answered/Accept', 'Proposal Approved/Design']:
            answer_code = tree.xpath('//span[@id="frm_fieldAnswercode_textEscaped"]/text()')[0].strip()
            print 'answer_code: '.ljust(20), answer_code
        elif status_phase in ['Proposed/Design']:
            answer_code = tree.xpath('//input[@id="frm_fieldAnswercode_inputSelectInput"]/@value')[0].strip()
            print 'answer_code: '.ljust(20), answer_code
        else:
            pass
            #print '--------------------------abnormal:', tr_num
    except Exception, ex:
        print 'Error for:', tr_num, ' with bad response:\n', resp.text
        raise resp.text

def parse_tr_list2(product):
    #for x in urls.values():
    #    resp = http_get(x)
    #    tree = html.fromstring(resp.text.encode('utf-8'))
    #    count = tree.xpath('//input[@id="j_id_28"]/@value')
    #    print count
    url = 'https://mhweb.ericsson.se/SearchWeb/faces/search/query/resultPage.xhtml?&v=3&queryKey=%s&rowsPerPage=All' %(product)
    resp = http_get(url)
    tree = html.fromstring(resp.text.encode('utf-8'))
    #trs = tree.xpath('//a[@class="searchlink"]/@href')
    #trs = tree.xpath('//a[@class="searchlink"]/text()')
    #trs1 = trs[::4]

    #for i in range(1, count+1):
    #    xp = '//tr[@id="resultTable:%s"]//span[@class="text"]/text()' %(i)
    #    it = tree.xpath(xp)
    #    print it
    #    break
    #count = tree.xpath('//input[@id="j_id_28"]/@value')
    #print count
    tr1 = tree.xpath('//tr[@class="rf-dt-r"] | //tr[@class="rf-dt-r rf-dt-fst-r"]')
    #tr1 = tree.xpath('//tr[@class="rf-dt-r"]//span[@class="text"]/text()')
    #subt = tr1[0::8]
    #cc = 0
    #for item in subt:
    #    print cc, ':', item
    #    cc += 1
        
    print len(tr1)
    #start = time.time()
    for item in tr1:
        t1 = item.xpath('.//a[@class="searchlink"]/text()')
        t2 = item.xpath('.//span[@class="text"]/text()')
        if len(t1) != 4:
            num = t1[0]
            print t1
        else:
            (num, author, handler) = (t1[0], t1[2], t1[3])
        if len(t2) == 9:
            (heading, market, priority, status, answer, reg_date, pp_date, ta_date, fi_date) = (i for i in t2)
        elif len(t2) == 8:
            if t2[1].strip() in ['A', 'B', 'C']:
                (heading, priority, status, answer, reg_date, pp_date, ta_date, fi_date) = (i for i in t2)
                market = 'N/A'
            else:
                (heading, market, priority, status, answer, reg_date, pp_date, ta_date) = (i for i in t2)
                fi_date = 'N/A'
        elif len(t2) == 7:
            
            (heading, priority, status, answer, reg_date, pp_date, ta_date) = (i for i in t2)
            (market, fi_date) = ('N/A', 'N/A')
        else:
            print t2
        #if len(t2) < 9 :
        #    print num.ljust(8), '|', market.ljust(20), '|', priority.ljust(3), '|', fi_date
        #print t2
    #stop = time.time()
    #print '==Sub Timecost: %.3f seconds==' %(stop-start)

###############################################################################################################
#                           Common functions
###############################################################################################################

###############################################################################################################
#                           Specified functions
###############################################################################################################
configs = {}
def get_config():
    with open('/home/led/scripts/config') as f:
        lines = f.readlines()
        for line in lines:
            if ':' in line:
                items = line.split(':')
                configs[items[0].strip()] = items[1].strip()

def http_get(url):
    '''
    learn https and authentication in requests
    learn real github example gist
    task:
       get your account's created date using authentication
    '''
    user = configs['user']
    passwd = configs['local_pwd']
    #passwd = getpass.getpass('Password:')

    resp = requests.get(url, auth=HTTPBasicAuth(user,passwd))
    return resp
    
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
    
def parse_tr_details(tr_num):
    '''
    Open the specified TR page and get the detail information.
    '''
    
    url = 'https://mhweb.ericsson.se/TREditWeb/faces/oo/object.xhtml?eriref=%s' %(tr_num)
    resp = http_get(url)
    tree = html.fromstring(resp.text.encode('utf-8'))
    
    print 'number: '.ljust(20), tr_num
    heading =  tree.xpath('//td[@class="valueStyleClass"]/span[@id="frm_fieldHeading_value"]//span[@class="valueStyleClass"]/text()')[0].strip()
    print 'heading: '.ljust(20), heading
    status_phase = tree.xpath('//div[@class="rf-cp-lbl-exp"]//span[@class="headingLabelValue"]/text()')[0].strip()
    print 'status_phase: '.ljust(20), status_phase
    #tree.xpath('//[@=""]/text()')[0]
    cur_mho = tree.xpath('//div[@class="rf-cp-lbl-exp"]//a[@class="headingLabelValue"]/text()')[0].strip()
    print 'cur_mho: '.ljust(20), cur_mho
    project = tree.xpath('//span[@id="frm_fieldCustomer_value"]//span[@class="valueStyleClass"]/text()')[0].strip()
    print 'project: '.ljust(20), project
    product = tree.xpath('//div[@id="frm_fieldOriginalProductRstate_product"]//td[@class="valueStyleClass"]//span/text()')[1].strip()
    rstate = tree.xpath('//div[@id="frm_fieldOriginalProductRstate_product"]//td[@class="valueStyleClass"]//span/text()')[3].strip()
    print 'product & r-state: '.ljust(20), product, rstate
    priority = tree.xpath('//span[@id="frm_fieldPriority_textEscaped"]/text()')[0].strip()
    print 'priority: '.ljust(20), priority
    
    if status_phase in ['Finished/Archive', 'Answered/Accept', 'Proposal Approved/Design']:
        answer_code = tree.xpath('//span[@id="frm_fieldAnswercode_textEscaped"]/text()')[0].strip()
        print 'answer_code: '.ljust(20), answer_code
    elif status_phase in ['Proposed/Design']:
        answer_code = tree.xpath('//input[@id="frm_fieldAnswercode_inputSelectInput"]/@value')[0].strip()
        print 'answer_code: '.ljust(20), answer_code
    else:
        answer_code = 'N/A'
        pass
        #print '--------------------------abnormal:', tr_num
        
    if status_phase in ['Finished/Archive', 'Assigned/Design']:
        author = tree.xpath('//*[@id="frm_fieldPrimtechinfo_input"]//span[@class="valueStyleClass"]/text()')[0]
    else:
        author = tree.xpath('//*[@id="frm_fieldPrimtechinfo_input"]//input[@id="frm_fieldPrimtechinfo_inputText"]/@value')[0]
    print 'author: '.ljust(20), author
    
    return (tr_num, priority, status_phase, answer_code, cur_mho, project, rstate, author)

urls = {
    'BDC_14A' : '46582',
    'BDC_15A' : '46583',
    'BDC_15B' : '53411',
    'BDC_16A' : '56395',
    'BDC_16B' : '64954',
    'BMC_15A' : '52759',
    'BMC_15B' : '65104',
    'BMC_16B' : '37589',
}

def parse_tr_list(product):
    '''
    Parse the abbreviate TR information from the searched result of an appointed product. For example "BDC_15A"
    '''
    url = 'https://mhweb.ericsson.se/SearchWeb/faces/search/query/resultPage.xhtml?&v=3&queryKey=%s&rowsPerPage=All' %(product)
    resp = http_get(url)
    tree = html.fromstring(resp.text.encode('utf-8'))
    tr1 = tree.xpath('//tr[@class="rf-dt-r"] | //tr[@class="rf-dt-r rf-dt-fst-r"]')
    print len(tr1)
    
    rf = open('/tmp/tr_info.txt', 'w')

    for item in tr1:
        t1 = item.xpath('.//a[@class="searchlink"]/text()')
        t2 = item.xpath('.//span[@class="text"]/text()')

        if len(t1) != 4:
            (num, author, handler) = (t1[0], t1[2], t1[2])
            print t1
        else:
            (num, author, handler) = (t1[0], t1[2], t1[3])

        if t2[1].strip() in ['A', 'B', 'C']:
            if t2[2].strip() in ['RE', 'AS']:
                (heading, priority, status, reg_date) = (i for i in t2[0:4])
                (market, answer, pp_date, ta_date, fi_date) = tuple(['N/A' for i in range(5)])
            elif t2[2].strip() in ['PP', 'PA']:
                (heading, priority, status, answer, reg_date, pp_date) = (i for i in t2[0:6])
                (market, ta_date, fi_date) = tuple(['N/A' for i in range(3)])
            elif t2[2].strip() in ['PO', 'TA']:
                (heading, priority, status, answer, reg_date, pp_date, ta_date) = (i for i in t2[0:7])
                (market, fi_date) = tuple(['N/A' for i in range(2)])
            elif t2[2].strip() in ['FI']:
                (heading, priority, status, answer, reg_date, pp_date, ta_date, fi_date) = (i for i in t2)
                market = 'N/A'
            else:
                print t2
        elif t2[2].strip() in ['A', 'B', 'C']:
            if t2[3].strip() in ['RE', 'AS']:
                (heading, market, priority, status, reg_date) = (i for i in t2[0:5])
                (answer, pp_date, ta_date, fi_date) = tuple(['N/A' for i in range(4)])
            elif t2[3].strip() in ['PP', 'PA']:
                (heading, market, priority, status, answer, reg_date, pp_date) = (i for i in t2[0:7])
                (ta_date, fi_date) = tuple(['N/A' for i in range(2)])
            elif t2[3].strip() in ['PO', 'TA']:
                (heading, market, priority, status, answer, reg_date, pp_date, ta_date) = (i for i in t2[0:8])
                fi_date = 'N/A'
            elif t2[3].strip() in ['FI']:
                (heading, market, priority, status, answer, reg_date, pp_date, ta_date, fi_date) = (i for i in t2)
            else:
                print t2
        else:
            print t2 
            
        line = '||'.join([num.ljust(8), author.ljust(8), handler.ljust(8), heading.ljust(100), market.ljust(20), priority.ljust(3), status.ljust(5), answer.ljust(4), reg_date.ljust(12), pp_date.ljust(12), ta_date.ljust(12), fi_date.ljust(12)])
        rf.write(line + '\n')
    rf.close()
                        
def get_tr_list(product):
    '''
    Get the TR list of an appointed product type. For example "BDC_15A"
    '''
    url = 'https://mhweb.ericsson.se/SearchWeb/faces/search/query/resultPage.xhtml?&v=3&queryKey=%s&rowsPerPage=All' %(product)
    resp = http_get(url)
    tree = html.fromstring(resp.text.encode('utf-8'))
    tr1 = tree.xpath('//tr[@class="rf-dt-r"] | //tr[@class="rf-dt-r rf-dt-fst-r"]')
    print len(tr1)

    tr_list = []
    for item in tr1:
        t1 = item.xpath('.//a[@class="searchlink"]/text()')
        tr_list.append(t1[0])

    rf = open('/tmp/tr_info.txt', 'w')
    count = 1
    for tr in tr_list:
        printc('black', 'yellow', '=======================%s. %s========================' %(count, tr))
        #parse_single(tr)
        (tr_num, priority, status_phase, answer_code, cur_mho, project, rstate, author) = parse_tr_details(tr)
        line = '||'.join(list(parse_tr_details(tr)))
        rf.write(line+'\n')
        count += 1
        time.sleep(5)
    rf.close()
        

    

    
import sys
if __name__ == '__main__':
    get_config()
    start = time.time()
    #parse_tr_details('HT53242')
    parse_tr_list(urls['BMC_15A'])
    #get_tr_list(urls['BDC_16A'])
    #parse_single('HT53242')
    stop = time.time()
    print '==Total Timecost: %.3f seconds==' %(stop-start)


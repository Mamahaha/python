#!/usr/bin/python


########## Variables, need to be updated before running the script
refresh_content_interval = 3300 #seconds, only used for refresh_content_static()

delivery_session_instance_id = 362
content_id = 255

file_url = [
'http://10.0.10.179/ejjewwn/1.mpd',
'http://10.0.10.179/ejjewwn/2.mpd',
]

add_rcq    = './addContent.rcq'
remove_rcq = './removeContent.rcq'
result_path   = '/var/tmp/rcq_result'

########### Common Functions ################
def generate_add_rcq(cid):
    print '[INFO]: Start generating AddContent request...'
    server_url = 'http://10.0.50.191:8080/bm-sc/mdf-cp/nbi/deliverySession/addContent/%d?origin=localhost' %(delivery_session_instance_id)
    
    rcq_head = '<?xml version="1.0" encoding="UTF-8"?>\n<rest-client version="2.5"><request><http-version>1.1</http-version><http-follow-redirects>false</http-follow-redirects><URL>%s</URL><method>PUT</method><headers><header key="Content-Type" value="application/xml"/></headers><body content-type="text/plain" charset="UTF-8">&lt;AddContent Version="1.0" xmlns="http://www.embmsbmscnbi.com"&gt;&#x0D;\n    &lt;OnDemand ContentId="%d"&gt;&#x0D;' %(server_url, cid)
    
    rcq_body = ''
    for i in file_url:
        file_info = '\n        &lt;OnDemandFile&gt;&#x0D;\n            &lt;FileURI&gt;%s&lt;/FileURI&gt;&#x0D;\n            &lt;UEcacheControl&gt;&#x0D;\n                &lt;NoCache&gt;true&lt;/NoCache&gt;&#x0D;\n            &lt;/UEcacheControl&gt;&#x0D;\n        &lt;/OnDemandFile&gt;&#x0D;' %(i)
        rcq_body += file_info
        
    rcq_tail = '\n    &lt;/OnDemand&gt;&#x0D;\n    &lt;BaseURL&gt;http://10.170.65.221:8070&lt;/BaseURL&gt;&#x0D;\n&lt;/AddContent&gt;</body></request></rest-client>'
    
    rcq = rcq_head + rcq_body + rcq_tail
    write_file(rcq, add_rcq)
    print '[INFO]: End of generating AddContent request.'
    

def generate_remove_rcq(cid):
    print '[INFO]: Start generating RemoveContent request...'
    server_url = 'http://10.0.50.191:8080/bm-sc/mdf-cp/nbi/deliverySession/removeContent/%d?origin=localhost' %(delivery_session_instance_id)
    
    rcq = '<?xml version="1.0" encoding="UTF-8"?>\n<rest-client version="2.5"><request><http-version>1.1</http-version><http-follow-redirects>false</http-follow-redirects><URL>%s</URL><method>PUT</method><headers><header key="Content-Type" value="application/xml"/></headers><body content-type="text/xml" charset="UTF-8">&lt;RemoveContent xmlns="http://www.embmsbmscnbi.com" Version="1.0"&gt;\n    &lt;Abort&gt;true&lt;/Abort&gt;\n    &lt;ContentId&gt;%d&lt;/ContentId&gt;\n&lt;/RemoveContent&gt;\n</body></request></rest-client>' %(server_url, cid)
    write_file(rcq, remove_rcq)
    print '[INFO]: End of generating AddContent request.'
    
def write_file(content, file_path):
    try:
        file = open(file_path, 'w')
        file.write(content)
        file.close()
    except Exception, ex:
        print '[Error]: Failed to write file.' %file_path
        raise 

def printc(bgc,fgc, str):
    print '\033[5m\033[%d;%dm%s\033[0m' %(bgc, fgc, str)
  
def display_usage():
    print '\n*=======================================================================================================================*'
    print '\033[7m* Name        : mwc_demo_tool'
    print '* Description : This tool is used to send AddContent request automatically to BDC periodically.'
    print '* Usage       : ./mwc_demo_tool.py refresh\033[0m'
    print '*=======================================================================================================================*\n'
    
import subprocess
def run_cmd(cmd):
    '''
    use subprocess.popen() to run commands
    '''
    try:
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (result, err) = p.communicate(cmd)
        return (result, err)
    except Exception, ex:
        print '[Error]: Failed to run command <%s>.' %cmd
        raise 

import time
def refresh_content_static():
    global content_id
    
    while True:
        print '[INFO]: Start refreshing content'

        run_cmd('rm -f *.rcq')
        generate_add_rcq(content_id)
        content_id += 1

        run_cmd('mkdir -p %s' %(result_path))
        run_cmd('rm -f %s/*' %(result_path))

        run_cmd('java -jar restclient-cli-2.5-jar-with-dependencies.jar %s -o %s' %(add_rcq, result_path))

        print '[INFO]: Result of AddContent:'
        (result, err) = run_cmd('cat %s/*.rcs' %(result_path))
        lines = result.split('\n')
        for line in lines:
            printc(32, 49, line)
            
        print '[INFO]: End of refreshing content. Sleep for %d seconds.' %(refresh_content_interval)
        time.sleep(refresh_content_interval)

from datetime import datetime
def refresh_content_dynamic():
    global content_id
    
    while True:
        now = datetime.now()
        interval = (60 - int(now.minute)) * 60 - int(now.second)
        print '[INFO]: Next AddContent will be triggered after %d seconds.' %(interval)
        time.sleep(interval)
        
        print '[INFO]: Start refreshing content at:', datetime.now()

        run_cmd('rm -f *.rcq')
        generate_add_rcq(content_id)
        content_id += 1

        run_cmd('mkdir -p %s' %(result_path))
        run_cmd('rm -f %s/*' %(result_path))

        run_cmd('java -jar restclient-cli-2.5-jar-with-dependencies.jar %s -o %s' %(add_rcq, result_path))

        print '[INFO]: Result of AddContent:'
        (result, err) = run_cmd('cat %s/*.rcs' %(result_path))
        lines = result.split('\n')
        for line in lines:
            printc(32, 49, line)
        time.sleep(30)

########### Test Function ################
def test_refresh():
    while True:
        now = datetime.now()
        interval = (60 - int(now.minute)) * 60 - int(now.second)
        print 'Original time: %s' %(now), ', will wait for: %d' %(interval) 
        time.sleep(interval)
        
        print 'Current time:', datetime.now().minute, datetime.now().second
        time.sleep(10)

########### Main ################
import sys
if __name__ == '__main__':
    if len(sys.argv) != 2:
        display_usage()
        #print 'ERROR: parameter count is wrong:', len(sys.argv)
        exit(1)
        
    mode = sys.argv[1].lower()
    if mode == 'gen_rcq':
        generate_add_rcq(content_id)
        generate_remove_rcq(content_id)
    elif mode == 'refresh':
        #refresh_content_static()
        refresh_content_dynamic()
    else:
        display_usage()
else:
    test_refresh()

'''
Created on Feb 26, 2016

@author: led
'''

common_functions = {
    'init_logger'         : lambda p1: init_logger(p1),
    'get_formatted_time'  : lambda : print_cur_time(),
    'parse_xml'           : lambda p1: xml_parser(p1),
    'run_local_cmd'       : lambda p1 : run_local_cmd(p1),
    'run_remote_cmd'      : lambda p1,p2,p3,p4,p5 : run_remote_cmd(p1, p2, p3, p4, p5),
    'sftp_tranport'       : lambda p1,p2,p3,p4,p5,p6 : transport_file(p1, p2, p3, p4, p5, p6),
    
}

import logging
def init_logger(file_path):
    '''
    '''
    logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s [%(levelname)s] %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='%s' %file_path,
                filemode='w')

import time    
def print_cur_time():
    '''
    '''
    print time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))

import xml.etree.ElementTree as ET
def xml_parser(file_path='common-xml.xml'):    
    try:
        tree = ET.parse(file_path)
    except Exception, e:
        print 'Failed to parse file <%s> with error: %s' %(file_path, e)
 
    ns_config = 'http://org.xml/common-config'
    root = tree.getroot() 
    category = root.find('./{%s}env/{%s}category' %(ns_config, ns_config)).text
    print category
    nodes = root.findall('./{%s}env/{%s}node' %(ns_config, ns_config))
    for node in nodes:
        ip = node.find('./{%s}ip' %(ns_config)).text
        print ip
 
import subprocess   
def run_local_cmd(cmd):
    '''
    Execute a shell command in local environment 
    '''
    try:
        handle = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        result = str.strip(handle.stdout.read())
        return result
    except Exception, e:
        print 'Failed to run local command <%s> with error: %s' %(cmd, e)

import paramiko
def run_remote_cmd(host, port, user, password, cmd):
    '''
    Execute a shell command in remote environment via SSH
    '''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password, port=port, allow_agent=False, look_for_keys=False)
    except Exception, e:
        ssh.close()
        print 'Failed to run remote command <%s> on host <%s> with error: %s' %(cmd, host, e)

    (_, stdout, stderr) = ssh.exec_command(cmd)
    if stderr.readlines() != '':
        ssh.close()
        print 'Failed to run remote command <%s> to host <%s> with error: %s' %(cmd, host, stderr.read())
    
    out = stdout.readlines()
    ssh.close()
    return out
        
def transport_file(host, port, user, password, operation, local_path, remote_path):
    '''
    Use SFTP client to upload/download a file to/from SFTP server 
        operation:
            'd'  : download mode
            'u'  : upload mode 
    '''
    try:
        trans=paramiko.Transport((host, port))
        trans.connect(username=user, password=password)
        sftp=paramiko.SFTPClient.from_transport(trans)
        if operation == 'd':
            sftp.get(remote_path, local_path)
        elif operation == 'u':
            sftp.put(local_path, remote_path)
        trans.close()
    except Exception, e:
        print 'Failed to transport file between local <%s> and remote <%s> to host <%s> with error: %s' %(local_path, remote_path, host, e)

def encrypt_password(password, key='shbuss'):
    '''
    '''
    result = run_local_cmd('echo %s |openssl aes-256-cbc -e -base64 -k %s' %(password, key))
    print 'before:<%s> after:<%s>'%(password, result)
    return result
 
def decrypt_password(encrypted_password, key='shbuss'):
    '''
    '''
    result = run_local_cmd('echo %s |openssl aes-256-cbc -d -base64 -k %s' %(encrypted_password, key))
    print 'before:<%s> after:<%s>'%(encrypted_password, result)
    return result

def test_operation(index):
    cur = time.time()
    a = 1
    for i in range(10000000):
        a += i
        a /= 3
    cost = time.time() - cur
    print '%s result: %s, cost: %s' %(index, a, cost)

def single_thread_run(operation, params):
    '''
    '''
    cur = time.time()
    for i in params:
        operation(i)
    cost = time.time() - cur
    print 'SingleThreadRun total time cost: %s' %cost

import multiprocessing as mul
from multiprocessing.pool import ThreadPool
def multi_thread_run(thread_num, operation, params):
    '''
    use pool.map()
    Result: very bad. even slower than single_thread_run
    '''
    cur = time.time()
    pool = ThreadPool(thread_num)
    results = pool.map(operation, params)
    pool.close()
    pool.join()
    cost = time.time() - cur
    print 'MultiThreadRun total time cost: %s' %cost
    for item in results:
        print item

def multi_thread_run2(op, params):
    '''
    use pool.apply_async
    Result: works well
    '''
    cur = time.time()
    result_list = []
    pool = mul.Pool()
    for n in params:
        result_list.append(pool.apply_async(op, args=(n,)))
    pool.close()
    pool.join()
    for result in result_list:
        result.get()
    cost = time.time() - cur
    print 'MultiThreadRun2 total time cost: %s' %cost

def multi_thread_run3(op, params):
    '''
    use pool.apply
    Result: the same as single_thread_run 
    '''
    cur = time.time()
    result_list = []
    pool = mul.Pool()
    for n in params:
        result_list.append(pool.apply(op, args=(n,)))
    pool.close()
    pool.join()
    #for result in result_list:
    #    result.get()
    cost = time.time() - cur
    print 'MultiThreadRun2 total time cost: %s' %cost
    

import re
def validate_ipv6(ipv6):
    '''
    check if the input ip is a valid IPV6 address. Exception will be raised if it's invalid
    '''
    pt = r'^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$'
    print re.match(pt, ipv6, re.M|re.I).group()


if __name__ == '__main__':
    #xml_parser('common-xml.xml')
    
    #psd = encrypt_password('embms1234', 'shbuss')
    #decrypt_password(psd, 'shbuss')
    
    #single_thread_run(test_operation, [1,2,3,4])
    #multi_thread_run(4, test_operation, [1,2,3,4])
    #multi_thread_run2(test_operation, [1,2,3,4])
    multi_thread_run3(test_operation, [1,2,3,4])
    #print mul.cpu_count()

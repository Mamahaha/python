#!/usr/bin/python
'''
Created on Dec 23, 2015
'''

import os
import json
import time
import signal
import threading
import logging
import ConfigParser
import subprocess
from multiprocessing.pool import ThreadPool
from datetime import datetime


#=============================common functions======
def init_logger():
    logging.basicConfig(filename='status_checker.log', format='%(asctime)s [%(levelname)s]:%(message)s', level=logging.DEBUG)
    logging.debug('Oh my god! I\'m shafa!')
    logging.warn('Sigh. I\'m bandeng')
    logging.info('Sh*t! I\'m diban')    

def parse_config():
    config = ConfigParser.ConfigParser()
    config.readfp(open('config'))
    print config.getint('yo yo', 'a')
    print config.get('yo yo', 'b')
    print config.get('yo yo', 'c')
    print config.get('yo yo', 'd')

def run_cmd1(cmd):
    '''Use os.popen() to run commands'''
    print 'Trying to run command:', cmd
    p = os.popen(cmd)
    return p.read().strip()

def run_cmd2(cmd):
    '''Use subprocess.popen() to run commands'''
    timeout = 10
    start = datetime.now()
    
    result = None
    print 'Run command:', cmd
    try:
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        while p.poll() is None:
            time.sleep(0.2)
            now = datetime.now()
            if (now - start).seconds > timeout:
                os.kill(p.pid, signal.SIGKILL)
                os.waitpid(-1, os.WNOHANG)
                print 'timeout for cmd:', cmd
                return None
        (result, err) = p.communicate(cmd)
        #print result
    except Exception, ex:
        print '[run_cmd] Exception:', ex
    return result.strip()
        
def pool_run_cmds(cmds):
    pool = ThreadPool(4)
    results = pool.map(run_cmd2, cmds)
    pool.close()
    pool.join()
    print results

#===================load config with ConfigParser==============================
class ConfigLoader():
    nodes = {}
    candidate_cmds = {}
    _config = ConfigParser.ConfigParser()
    
    def __init__(self, config_file):
        self._config.readfp(open(config_file))
    
    def _load_nodes(self):
        #print 'load node'
        items = self._config.items('BMC LIST')        
        for item in items:
            self.nodes[item[0]] = item[1]
        #print self.nodes
        
    def _load_candidates(self):
        #print 'load candidate'        
        items = self._config.items('CANDIDATE COMMAND LIST')        
        for item in items:
            if item[1] == '1':
                self.candidate_cmds[item[0]] = {}
        #print self.candidate_cmds
        
    def _load_cmds(self):
        #print 'load cmd'
        items = self._config.items('BMC STATUS COMMAND')
        for item in items:
            if item[0] in self.candidate_cmds.keys():
                self.candidate_cmds[item[0]]['cmd'] = item[1]
        #print self.candidate_cmds
        
    def _load_expected_results(self):
        #print 'load expectation'
        items = self._config.items('BMC STATUS RESULT')
        for item in items:
            if item[0] in self.candidate_cmds.keys():
                self.candidate_cmds[item[0]]['expectation'] = item[1]
        #print self.candidate_cmds
    
    def _load_output(self):
        #print 'load output'
        items = self._config.items('BMC STATUS OUTPUT')
        for item in items:
            if item[0] in self.candidate_cmds.keys():
                self.candidate_cmds[item[0]]['true'] = item[1].split(';')[0]
                self.candidate_cmds[item[0]]['false'] = item[1].split(';')[1]
        #print self.candidate_cmds
        
    def _validate_cmds(self):
        temp_result = {}
        for item in self.candidate_cmds.keys():
            if len(self.candidate_cmds[item]) == 4:
                temp_result[item] = self.candidate_cmds[item]
        self.candidate_cmds = temp_result
        
    def load_config(self):
        self._load_nodes()
        self._load_candidates()
        self._load_cmds()
        self._load_expected_results()
        self._load_output()
        self._validate_cmds()
        #print self.nodes
        #print self.candidate_cmds
        
#===================load config with json==============================
class JsonConfigLoader():
    nodes = {}
    candidate_cmds = {}
    def __init__(self):
        pass
    
    def load_config(self, config_file):         
        with open(config_file, 'r') as f:
            data = json.load(f)
        self.nodes = data['nodes']
        cmd_list = data['command-list']
        for item in cmd_list:
            if cmd_list[item] == 1:
                self.candidate_cmds[item] = data[item]
        #print self.nodes
        #print self.candidate_cmds
    def run_and_check(self, param):
        (node_name, cmd_name) = param.split(';')
        cmd = 'ssh %s "%s"' %(self.nodes[node_name], self.candidate_cmds[cmd_name]['cmd'])
        exp = self.candidate_cmds[cmd_name]['expect']
        result = run_cmd2(cmd)
        if result == exp:
            return '%s;'.ljust(8-len(node_name)) %(node_name) + '%s;'.ljust(25-len(cmd_name)) %(cmd_name) + self.candidate_cmds[cmd_name]['true']
            #return node_name.ljust(10) + ";"  + cmd_name.ljust(20) + ";" + self.candidate_cmds[cmd_name]['true']
        else:
            return '%s;'.ljust(8-len(node_name)) %(node_name) + '"%s;'.ljust(25-len(cmd_name)) %(cmd_name) + self.candidate_cmds[cmd_name]['false']
    def multi_run_and_check(self, params):
        pool = ThreadPool(4)
        results = pool.map(self.run_and_check, params)
        pool.close()
        pool.join()
        print 'NODE'.ljust(6) + 'COMMAND'.ljust(23) + 'RESULT'
        for item in results:
            print item
    def _write_file(self, config_file):
        ss = {
        'check-event-port' : 
        {   
            'description' : "Check if event port 8055 is ready",
            'cmd' : "netstat -an | grep 9889 | grep -v grep | grep LISTEN | wc -l",
            'expect': "2",
            'true': "OK",
            'false': "NOK"
        },
        "check-karaf-process" :
        {
            'description' : "Check if karaf process is running",
            'cmd': "ps -ef | grep java | grep -v grep | wc -l",
            'expect': "1",
            'true': "GOOD",
            'false': "BAD"
        }}
        with open(config_file, 'w') as f:
            json.dump(ss, f, indent=4)
        
#=============================check status of all nodes======
class check_status_thread(threading.Thread):
    def __init__(self, threadId, name, check_cmd):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.name = name
        self.check_cmd = check_cmd
    def run(self):
        count = 0
        while count < 5:
            time.sleep(3)
            count += 1
            print '%s start %s' %(self.name, time.ctime(time.time()))
def check_single_status(node_name, check_cmd):
    None

def check_all_nodes():
    bmcs = ('bmc1', 'bmc2')
    ts = []
    i = 1
    for bmc in bmcs:
        t = check_status_thread(i, bmc, 'hahaa')
        ts.append(t)
        t.start()
        i += 1
    for t in ts:
        t.join(100)
    print 'Finished checking the status of all nodes'

#=============================test section===================
def test_cmd():
    config = ConfigParser.ConfigParser()
    config.readfp(open('config'))
    cmd = config.get('BMC STATUS COMMAND', 'check_event_port')
    exp = config.get('BMC STATUS CHECK', 'check_event_port')
    result = run_cmd1(cmd)
    if result == exp:
        print 'Good status'
    else:
        print 'Bad status:', result
def test_multi_cmds():
    #cmds = ['cat ~/scripts/set_route.sh', 'curl -oO http://wiki.jikexueyuan.com/project/the-python-study-notes-second-edition/operating-system.html', 
    #        'ls -al ~/ | grep workspace', 'ps -ef  | grep 9889 | grep -v grep', 'ls /tmp/ | grep gc']
    cmds = ['curl -oO http://wiki.jikexueyuan.com/project/the-python-study-notes-second-edition/operating-system.html']
    pool_run_cmds(cmds)
    
def test_config_loader():
    cl = ConfigLoader('config')
    cl.load_config()
def test_json_config_loader():
    cl = JsonConfigLoader()
    cl.load_config('config_json')
def test_json_multi_cmds():
    cl = JsonConfigLoader()
    cl.load_config('config_json')
    params = ['%s;%s' %(i, j) for i in cl.nodes for j in cl.candidate_cmds]
    cl.multi_run_and_check(params)
    

#=============================main section===================
if __name__ == '__main__':
    #init_logger()
    #parse_config()
    #check_all_nodes()
    #test_multi_cmds()
    #test_config_loader()
    #test_json_config_loader()
    test_json_multi_cmds()

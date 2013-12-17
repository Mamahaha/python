#!/usr/bin/python
import os
import re
import sys
import json
import types
import datetime
import subprocess

#######Class Section#########
class GitLogReviewer:
    '''A tool used to parse git log'''
    __jsonList = []
    __resultList = []
    __loadStatus = False
    __parseStatus = False
    __abandonCount = 0
    #Below params are used only when querying from command
    __limit = 500
    __sortKey = None
    __endFlag = False
    __gitCmd = '' # your git server access command
    
    def __init__(self, limit):
        if limit >= 0:
            self.__limit = limit
        
    def loadGitCfg(self, cfgPath):
        try:
            fh = open(cfgPath)
            lines = fh.readlines()
            fh.close()
            for line in lines:
                subLine = line.strip()
                if subLine.startswith('url'):
                    list1 = subLine.split('=')
                    str0 = list1[1].lstrip()
                    str1 = str0.lstrip('ssh://')
                    list2 = str1.split(':')
                    url = list2[0]
                    list3 = list2[1].split('/')
                    port = list3[0]
                    proj = list2[1].lstrip(port + '/')
                    self.__gitCmd = 'ssh -p %s %s gerrit query --format=JSON --patch-sets --all-approvals status:closed project:\"%s\" ' %(port, url, proj)
        except Exception, ex:
            print '[loadGitCfg] Exception:', ex
            print '[loadGitCfg] Trying default Git command...'
        finally:
            if self.__limit > 0:
                self.__gitCmd += " limit:%d" %(self.__limit)
            print self.__gitCmd
    
    def loadGitCfg2(self, cfgPath):
        try:
            fh = open(cfgPath)
            line = fh.readline()
            found1 = False
            found2 = False
            p1 = re.compile(r'(\s)*\[remote(\s)+\"origin\"\]')
            p2 = re.compile(r'(\s)*url(\s)*=(\s)*ssh://(\S)+:(\d)+/(\w)+')
            while line:
                #print line
                if p1.match(line):
                    found1 = True
                if found1 and p2.match(line):
                    found2 = True
                    break
                line = fh.readline()
            fh.close()
          
            if found2:
                l1 = line.strip()
                ll1 = re.compile(r'(\s)*url(\s)*=(\s)*ssh://').split(l1)
                ll2 = re.compile(r':').split(ll1[4])
                ll3 = re.compile(r'/').split(ll2[1])
                ll4 = re.compile(r'(\d)+/').split(ll2[1])
                url = ll2[0]
                port = ll3[0]
                proj = ll4[2]
                self.__gitCmd = 'ssh -p %s %s gerrit query --format=JSON --patch-sets --all-approvals status:closed project:\"%s\" ' %(port, url, proj)
            else:
                print '[loadGitCfg2] Error when loading git config' 
                print '[loadGitCfg2] Trying default Git command...'     
        except Exception, ex:
            print '[loadGitCfg2] Exception:', ex
            print '[loadGitCfg2] Trying default Git command...'
        finally:
            if self.__limit > 0:
                self.__gitCmd += " limit:%d" %(self.__limit)
            print self.__gitCmd
                
    def loadFromFile(self, filePath):
        try:
            fh = open(filePath, 'r')
            self.__jsonList = fh.readlines()
            self.__loadStatus = True
            fh.close()
        except Exception, ex:
            print '[loadFromFile] Exception:', ex
    
    def loadFromPipe(self):
        try:
            pipeStr = sys.stdin.read()
            self.__jsonList = pipeStr.split('\n')
            self.__loadStatus = True
        except Exception, ex:
            print '[loadFromPipe] Exception:', ex
    
    def loadFromCmd1(self, strCmd):
        '''Use os.popen() to run commands. Not recommended'''
        try:
            self.__jsonList = os.popen(strCmd)
            self.__loadStatus = True
        except Exception, ex:
            print '[loadFromCmd1] Exception:', ex
    
    def loadFromCmd2(self, strCmd):
        '''Use subprocess.popen() to run commands'''
        try:
            p = subprocess.Popen(strCmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            (strResult, strErr) = p.communicate(strCmd)
            self.__jsonList = strResult.split('\n')
            self.__loadStatus = True
        except Exception, ex:
            print '[loadFromCmd2] Exception:', ex
            
    def parseRecord(self, record):
        '''Return value:
           0 -> Record with right format
           1 -> Record with "ABANDONED" status
           2 -> Record with other formats that do not match requirement
        '''
        #print '1:'
        if type(record) != type('a'):
            return 2
        if record.find('project') == -1:
            return 2
    
        dict = json.loads(record)
        if 'id' not in dict:
            return 2;
        id = dict['id']
        
        if 'owner' not in dict or 'name' not in dict['owner']:
            return 2;
        name =  dict['owner']['name']
    
        if 'patchSets' not in dict or 'status' not in dict or 'sortKey' not in dict or 'createdOn' not in dict or 'lastUpdated' not in dict:
            return 2;
        if dict['status'] == 'ABANDONED':
            return 1;
        
        createDate = datetime.datetime.fromtimestamp(int(dict['createdOn']))
        #updateDate = datetime.datetime.fromtimestamp(int(dict['lastUpdated']))
        
        self.__sortKey = dict['sortKey']
        number = 0
        fail1 = 0
        fail2 = 0
        lastCommitCreateDate = ''
        lastSCMVerifyDate = ''
        reviewDate = ''
        submitDate = ''
        for item in dict['patchSets']:
            if 'number' not in item or 'approvals' not in item:
                continue
            number += 1
            
            
            for subItem in item['approvals']:
                if 'value' not in subItem:
                    continue
                if subItem['value'] == '-1':
                    fail1 += 1
                elif  subItem['value'] == '-2':
                    fail2 += 1
        #print '2', record
        lastItem = dict['patchSets'][len(dict['patchSets']) - 1]
        lastCommitCreateDate = datetime.datetime.fromtimestamp(int(lastItem['createdOn']))
        if 'approvals' not in lastItem:
            #print 'Bad record:', record
            return 2
        for subItem in lastItem['approvals']:
            if subItem['type'] == 'VRIF' and subItem['by']['name'] == 'New EMA SCM Account':
                lastSCMVerifyDate = datetime.datetime.fromtimestamp(int(subItem['grantedOn']))
            if subItem['type'] == 'CRVW':
                reviewDate = datetime.datetime.fromtimestamp(int(subItem['grantedOn']))
            if subItem['type'] == 'SUBM':
                submitDate = datetime.datetime.fromtimestamp(int(subItem['grantedOn']))
        
        self.__resultList.append("%s, %s, %d, %d, %d, %s, %s, %s, %s, %s" %(id, name, number, fail1, fail2, createDate, lastCommitCreateDate, lastSCMVerifyDate, reviewDate, submitDate))
        #print '4'
        return 0
    
    def parseAllRecords(self):
        if not self.__loadStatus:
            print '[parseAllRecords] Error when loading records'
            return

        #The last 2 elements are useless, ignore them.
        print '\n[parseAllRecords] Start parsing %d records.' %(len(self.__jsonList) - 2)
        if len(self.__jsonList) <= self.__limit:
            self.__endFlag = True
            
        self.__abandonCount = 0
        try:
            self.__resultList = []
            for item in self.__jsonList:
                if self.parseRecord(item) == 1:
                    self.__abandonCount += 1
            self.__parseStatus = True
            print '[parseAllRecords] %d records have been parsed successfully.' %(len(self.__resultList))
            print '[parseAllRecords] %d records with \'ABANDONED\' status have been ignored.\n' %(self.__abandonCount)
        except Exception, ex:
            print '[parseAllRecords] Exception:', ex

    def outputResult(self):
        if not self.__parseStatus: 
            return
        
        print 'Id,  Owner,  PatchsetNumber,  -1 Votes,  -2 Votes, FirstCommitCreateDate, LastCommitCreateDate, LastSCMVerifyDate, ReviewDate, SubmitDate'
        for item in self.__resultList:
            print item
        
    
    def save2File(self, filePath, newFlag = True):
        if not self.__parseStatus: 
            return
        
        try:
            print '[save2File] Save records to file: \'%s\'...' %(filePath)
            if newFlag:
                path = os.path.dirname(filePath)
                if path != '' and not os.path.exists(path):
                    os.makedirs(path)
                fh = open(filePath, 'w')
                fh.write('Id,  Owner,  PatchsetNumber,  -1 Votes,  -2 Votes,  FirstCommitCreateDate, LastCommitCreateDate, LastSCMVerifyDate, ReviewDate, SubmitDate\n')
            else:
                fh = open(filePath, 'a+')
            
            for item in self.__resultList:
                fh.write(item + '\n')
            fh.close()
            if self.__endFlag:
                print '[save2File] All records are saved successfully\n'
        except Exception, ex:
            print '[save2File] Exception:', ex
    
    def processFile(self, srcPath, resultPath):
        '''Retrieve records from file and parse them'''
        self.loadFromFile(srcPath)
        self.parseAllRecords()
        reviewer.save2File(resultPath, True)
        
    def processCmd(self, cfgPath, resultPath):
        '''Retrieve records from gerrit server and parse them'''
        self.loadGitCfg(cfgPath)
        self.loadFromCmd2(self.__gitCmd)
        self.parseAllRecords()
        self.__endFlag = True
        self.save2File(resultPath, True)
        
    def loopProcessCmd(self, cfgPath, resultPath):
        '''Loop retrieving records from gerrit server and parsing them'''
        self.loadGitCfg2(cfgPath)
        newFileFlag = True
        totalCount = 0
        totalAbandonCount = 0
        while not self.__endFlag:
            if self.__sortKey == None:
                #start
                cmd = self.__gitCmd
                newFileFlag = True
            else:
                #resume
                cmd = self.__gitCmd + ' resume_sortkey:%s' %(self.__sortKey)
                newFileFlag = False
            self.loadFromCmd2(cmd)
            self.parseAllRecords()
            self.save2File(resultPath, newFileFlag)
            
            totalCount += len(self.__resultList)
            totalAbandonCount += self.__abandonCount
            if not self.__loadStatus or not self.__parseStatus:
                print 'l:', self.__loadStatus, 'p:', self.__parseStatus
                break
        print '\n[loopProcessCmd] Totally %d records have been parsed successfully.' %(totalCount)
        print '[loopProcessCmd] Totally %d records with \'ABANDONED\' status have been ignored.\n' %(totalAbandonCount)
        
            

#######Function Section#########

    
#######Executing Section#########
if __name__ == '__main__':
    my_git_cfg = ''
    reviewer = GitLogReviewer(400)
    #reviewer.processCmd(None, 'result_once_def_061204.csv')
    reviewer.loopProcessCmd(my_git_cfg, 'git_result.csv')
    #reviewer.processCmd(my_git_cfg, 'result_loop_cfg_new2.csv')
    #reviewer.loopProcessCmd(None, 'result_loop_def.csv')
    #reviewer.processFile('origin_result', 'result3.csv')
    #reviewer.loadGitCfg('../cfg.txt')
    #reviewer.loadGitCfg2('../cfg.txt')






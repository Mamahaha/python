#!/usr/bin/python
#!C:/Python27/python.exe
import os
import re
import sys
import types
import anydbm
import time
import datetime
import subprocess
#sys.path.append('C:\\personal\\sys_env')
#import wincolor
if os.name == 'nt':
  import wincolor2

TEMP_FOLDER = 'C:\\Temp\\'
cpt = None
if os.name == 'nt':
  cpt = wincolor2.Color()


def printC(fgColor, bgColor, print_text):
  fgc = fgColor
  bgc = bgColor
  if fgColor == '':
    fgc = 'white'
  if bgColor == '':
    bgc = 'black'
  if os.name == 'nt':
    cpt.pt(fgc, bgc, print_text)
  else:
    print print_text,

def printlC(fgColor, bgColor, print_text):
  fgc = fgColor
  bgc = bgColor
  if fgColor == '':
    fgc = 'white'
  if bgColor == '':
    bgc = 'black'
  if os.name == 'nt':
    cpt.ptl(fgc, bgc, print_text)
  else:
    print print_text
  
def runCmd(strCmd):
  '''Use subprocess.popen() to run commands'''
  tempCmd = strCmd + ' > %scmdResult'%TEMP_FOLDER
  resultList = []
  try:
      p = subprocess.Popen(strCmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
      (strResult, strErr) = p.communicate(strCmd)
      resultList = strResult.split('\n')
  except Exception, ex:
      print '[runCmd] Exception:', ex
  return resultList

def getTime():
  return time.strftime("%Y%m%d_%H_%M", time.localtime())

def persistDict(fp, dataDict):
  flDB = anydbm.open(fp, 'c')
  for item in dataDict:
    flDB[item] = dataDict[item]
  flDB.close()

def reCheck(str, rule):
  if str == '' or str == None or rule == '' or rule == None:
    return False
  pattern = re.compile(r'%s'%rule)
  match = pattern.match(str)
  if match:
    return True
  else:
    return False
  

def getModuleName():
  curPath = os.getcwd()
  return curPath.split('\\')[-1]

def getRootPath():
  curPath = os.getcwd()
  moduleName = getModuleName()
  return curPath[0 : (len(curPath) - len(moduleName))]
    
def checkGitEnv():
  resultList = runCmd('git branch')
  if resultList[0] == '':
    printC('red', '', '[log] Not a valid GIT repository!')
    return False
  else:
    return True
      
def backupModifications(rootPath, moduleName):
  '''all modified files are stored in the same folder'''
  printlC('yellow', '', '[log] Start backing up modifications')
  #create a temp folder
  tempFolder = TEMP_FOLDER + moduleName
  runCmd('mkdir ' + tempFolder)  
 
  changeDict = {}
  resultList = runCmd('git status .')
  #backup modifications
  for line in resultList:
    if line.startswith('#'):
      line = line.lstrip('#').strip()
      if line.startswith('modified:'):
        filePath = line.lstrip('modified:').strip().replace('/', '\\')
        fileName = filePath.split('\\')[-1]
        changeDict[fileName] = filePath
        runCmd('cp ' + filePath + ' ' + tempFolder+ '\\' + fileName)
  
  #persist file paths
  persistDict(tempFolder+ '\\filelist.pdb', changeDict)

  
def backupModifications2(rootPath, moduleName):
  '''All modified files are stored with original folder'''
  printlC('yellow', '', '[log] Start backing up modifications')
  #create a temp folder
  tempFolder = TEMP_FOLDER + moduleName
  runCmd('mkdir ' + tempFolder)  
 
  changeDict = {}
  resultList = runCmd('git status .')
  #backup modifications
  for line in resultList:
    if line.startswith('#'):
      line = line.lstrip('#').strip()
      if line.startswith('modified:'):
        filePath = line.lstrip('modified:').strip().replace('/', '\\')
        fileName = filePath.split('\\')[-1]
        runCmd('mkdir ' + tempFolder + '\\' + filePath.rstrip(fileName))
        changeDict[fileName] = filePath
        runCmd('cp ' + filePath + ' ' + tempFolder+ '\\' + filePath)

def backupPatches(rootPath, moduleName):
  printlC('white', '', '[log] Start backing up patches')
  tempFolder = TEMP_FOLDER + moduleName
  runCmd('mkdir ' + tempFolder)
  
  runCmd('git diff > unstaged.patch')
  runCmd('git diff --cached > staged.patch')
  runCmd('git diff --stat > abbrevunstaged.patch')
  runCmd('mv *.patch ' + tempFolder + '\\')

def displayPatch(rootPath, moduleName, patchName):
  printlC('white', '', '[log] Show ' + patchName)
  tempFolder = TEMP_FOLDER + moduleName
  fh = open(tempFolder + '\\' + patchName, 'r')
  printC('black', '', '\n')
  printlC('green', 'blue', '\n======================Display "%s" start==================================================================================='%patchName)
  lines = fh.readlines()
  for line in lines:
    if line.startswith('diff --git'):
      printlC('yellow', '', line.strip('\n'))
    elif line.startswith('--- ') or line.startswith('+++ '):
      printlC('cyan', '', line.strip('\n'))
    elif line.startswith('-'):
      printlC('red', '', line.strip('\n'))
    elif line.startswith('+'):
      printlC('green', '', line.strip('\n'))
    elif line.startswith('@@ '):
      srcIndex = line.find('@@', 2)
      printC('lightmagenta', '', line[0:srcIndex+2])
      printC('white', '', line[srcIndex+3:])
    else:
      printlC('white', '', line.strip('\n'))
  printlC('green', 'blue', '\n======================Display "%s" stop==================================================================================='%patchName)
  printC('black', '', '\n')
  fh.close()
  
def restoreModifications(rootPath, moduleName):
  #printlC('white', '', '[log] Start restoring modifications')
  changeDict = {}
  tempFolder = TEMP_FOLDER + moduleName
  flDB = anydbm.open(tempFolder+ '\\filelist.pdb', 'r')
  for item in flDB:
    changeDict[item] = flDB[item]
  flDB.close()
  
  #restore modifications
  for (root, dirs, files) in os.walk(tempFolder, topdown=False):
    for name in files:      
      if changeDict.has_key(name):
        runCmd('cp ' + tempFolder + '\\' + name + ' ' + changeDict[name])


def searchParamInFolder(rootPath, moduleName, param, ignoredParam):
  tempFolder = TEMP_FOLDER + moduleName
  target = param
  if not param.startswith('~'):
    tempFolder = os.getcwd()
    target = param.lstrip('~')
  #printlC('green', '', 'loop folder: ' + tempFolder + ' ' + target)
  loopSearchFolder(tempFolder, target, ignoredParam)
  

def loopSearchFolder(folder, param, ignoredParam):
  #printlC('green', '', 'loop folder: ' + folder)
  for (root, dirs, files) in os.walk(folder, topdown=False):
    for fn in files:
      #if fn.split('.')[-1] in ['java', 'c', 'h', 'cpp',]:
        searchInFile2(os.path.join(root, fn), param, ignoredParam)
  
def searchInFile(filePath, param, ignoredParam):
  fh = open(filePath, 'r')
  lines = fh.readlines()
  fh.close()
  fileFlag = False
  lineFlag = False
  lineNo = 0
  for line in lines:
    lineNo += 1
    if reCheck(line, ignoredParam) == True:
      continue      
    newLine = line.strip()
    if line.find(param) != -1:
      if not fileFlag:
        fileFlag = True
        printC('white', '', 'Found')
        printC('yellow', '', param)
        printC('white', '', 'in file')
        printlC('lightmagenta', '', filePath.split('\\')[-1])
      if not lineFlag:
        lineFlag = True
        printlC('cyan', '', '%d :'%lineNo)
        printC('green', '', line)        
    else:
      if lineFlag:
        printC('green', '', line)
    if line.strip().endswith(';'):
        lineFlag = False

def searchInFile2(filePath, param, ignoredParam):
  fh = open(filePath, 'r')
  lines = fh.readlines()
  fh.close()
  fileFlag = False
  lineFlag = False
  lineNo = 0
  for line in lines:
    lineNo += 1
    if reCheck(line, ignoredParam) == True:
      continue      
    newLine = line.strip()
    if line.find(param) != -1:
      if not fileFlag:
        fileFlag = True
        printC('white', '', 'Found')
        printC('yellow', '', param)
        printC('white', '', 'in file')
        printlC('lightmagenta', '', filePath.split('\\')[-1])
      printlC('cyan', '', '%d :'%lineNo)
      printC('green', '', line)
        
def findFile(fn):
  curPath = os.getcwd()
  dirCmd = 'dir ' + curPath + '\\' + fn + ' /a/s/p'
  lines = runCmd(dirCmd)
  if lines[0].startswith('File Not Found'):
    printlC('red', '', 'No such file is found.')
    return
  
  fPath = ''
  fName = ''
  fCount = 0
  for item in lines:
    if item.strip() == '':
      continue
    
    if item.strip().startswith('Directory of'):
      fPath = item.strip().lstrip('Directory of ') + '\\'
      continue
    words = filter(lambda x : x!= '', item.strip().split(' '))
    if len(words) >= 5:
      if words[2] in ['AM', 'PM']:
        fCount += 1
        fName = words[4]
        runCmd('ue.lnk ' + fPath + fName)
  printC('yellow', '', '[Search&Open] Totally ')
  printC('red', 'yellow', '%d'%fCount)
  printC('yellow', '', 'files are found')
  
def removeBackupFiles(moduleName):
  tempFolder = TEMP_FOLDER + moduleName
  ipt = raw_input('[Alert] Are you sure you want to remove all files in "%s" [Y/N]? '%tempFolder)
  if ipt.lower() == 'y':
    runCmd('rm -rf %s'%tempFolder)

def compareModification(moduleName):
  tempFolder = TEMP_FOLDER + moduleName
  curPath = os.getcwd()
  runCmd('bc.lnk ' + tempFolder + ' ' + curPath)

def staticCheckModification(rootPath, moduleName):
  tempFolder = TEMP_FOLDER + moduleName
  c = 'java -jar ' + rootPath + '\\ValidateErrorLog_fat.jar ' + tempFolder + ' ' + rootPath + '\\bmsc-common\\error-definition\\bdc_error_definition.txt'
  #printlC('yellow', '', c)
  results = runCmd(c)
  resultFile = 'error_log_violation.txt'
  if len(results) >= 2:
    for item in results:
      printlC('red', '', item.strip())
      
    printlC('green', '', '\n======================Display "%s" start==================================================================================='%resultFile)
    fh = open(rootPath + '\\' + moduleName + '\\' + resultFile, 'r')
    resultLines = fh.readlines()
    for item in resultLines:
      ss = item.split('==>')      
      printC('yellow', '', ss[0] + ' ==>')
      printlC('cyan', '', ss[1])
    printlC('green', '', '======================Display "%s" stop==================================================================================='%resultFile)
  else:
    for item in results:
      printlC('green', '', item.strip())

#======================================================
def addDebugLog(fPath):
  fh = open(fPath)
  lines = fh.readlines()
  fh.close()
  
  newContent = ''
  funcName = ''
  count = 0
  funcFlag = False
  while count < len(lines):
    line = lines[count]
    count += 1
    if line.startswith(' ') or line.startswith('/'):
      newContent += line
      continue
    if reCheck(line, '\S.+::\w+\(.*\).*') and lines[count].startswith('{'):
      if funcFlag:
        newContent += line
        continue
      else:
        #print '====func flag becomes true <', line, '> content <', line, '>=========' 
        funcFlag = True
        funcName = line.split('(')[0].split(' ')[-1]
        newContent += line        
        newContent += lines[count]
        count += 1
        newContent += '    LogManager::instance()->getEventLog().log(Level::INFO, "LED_LOG", "Enter <' + funcName + '>");\n'
    elif line.startswith('}'):
      if funcFlag:
        #print '====func flag becomes false <', line, '> content <', line, '>=========' 
        newContent += '    LogManager::instance()->getEventLog().log(Level::INFO, "LED_LOG", "Leave <' + funcName + '>\n'
        funcFlag = False
      #else:
        #print '===========ERROR parsing in file <', fPath, '> line <', count , '>, content <', line, '>==========='
      newContent += line
    else:
      newContent += line
   
  fh = open(fPath, 'w')
  fh.write(newContent)
  fh.close()

def loopFiles():
  for (root, dirs, files) in os.walk(os.getcwd(), topdown=False):
    for fn in files:
      if fn.split('.')[-1] in ['cpp']:
        addDebugLog(os.path.join(root, fn))
     
  
      
    
#======================================================
def displayCmdList():
  printC('white', '', '[Usage] ')
  printlC('green', '', '> ga.py [command] [param]')
  printlC('lightmagenta', '', '\n [Command List]')
  printlC('yellow', '', ' 1 : Backup modified files')
  printlC('yellow', '', ' 2 : Backup patches')
  printlC('yellow', '', ' 3 : Display patches')
  printlC('cyan',   '', ' 4 : Search param in files -- param that starts with "~" will be searched in backup folder')
  printlC('yellow', '', ' 5 : Search files that match given file name and open them with UltraEdit')
  printlC('yellow', '', ' 6 : Compare folders')
  printlC('red',    '', ' 7 : Restore modified files -- deprecated')  
  printlC('yellow', '', ' 8 : Remove all backup files')
  printlC('yellow', '', ' 9 : Static check modifications')
  printlC('yellow', '', ' a : Search and count params')
  printlC('yellow', '', ' b : Add debug log in every function of MDF-UP')
  printlC('yellow', '', ' 0 : Exit\n')
  
def cmdManager(ipt, param, param2):
  #if not checkGitEnv():
  #  return
  rp = getRootPath()
  mn = getModuleName()
  
  while True:
    #ipt = raw_input('[command] Please input your command:')   #only used for loop
    if ipt == '1':
      backupModifications2(rp, mn)
    elif ipt == '2':
      backupPatches(rp, mn)
    elif ipt == '3':
      displayPatch(rp, mn, 'unstaged.patch')
      displayPatch(rp, mn, 'staged.patch')
      displayPatch(rp, mn, 'abbrevunstaged.patch')
    elif ipt == '4':
      searchParamInFolder(rp, mn, param, param2)      
    elif ipt == '5':
      findFile(param)      
    elif ipt == '6':
      compareModification(mn)      
    elif ipt == '7':
      None
      restoreModifications(rp, mn)       #not provided currently for security
    elif ipt == '8':
      removeBackupFiles(mn)
    elif ipt == '9':
      staticCheckModification(rp, mn)
    elif ipt == 'a':
      calFolders()
    elif ipt == 'b':
      None      
    elif ipt == '0':
      None
      #break                        #only used for loop
    else:
      displayCmdList()
    break                           #only used for one-time run

##########################################################
# 
##########################################################
def searchKeyInFile(fp, key):
  fh = open(fp, 'r')
  lines = fh.readlines()
  fh.close()
  fileFlag = False
  lineFlag = False
  lineNo = 0
  count = 0
  for line in lines:
    lineNo += 1
    if line.strip().startswith('//'):
      continue    
    newLine = line.strip()
    if line.find(key) != -1:
      count += 1
  return count

def searchKeyInFiles(pth, key):
  tCount = 0
  for (root, dirs, files) in os.walk(pth, topdown=False):
    for fn in files:
      if fn.endswith('.java') or fn.endswith('.cc') or fn.endswith('.cpp') or fn.endswith('.h') or fn.endswith('.hpp') or fn.endswith('.c'):
        tCount += searchKeyInFile(os.path.join(root, fn), key)
  return tCount

def calFiles(pth, comp, key):
  pth = os.path.join(pth, comp)
  #tcError = searchKeyInFiles(pth, 'Level::ERROR')
  #tcWarn = searchKeyInFiles(pth, 'Level::WARNING')
  #tcDebug = searchKeyInFiles(pth, 'Level::DEBUG_LOG')
  #tcInfo = searchKeyInFiles(pth, 'Level::INFO')
  #tcTrace = searchKeyInFiles(pth, 'Level::TRACE') 
  tcError = searchKeyInFiles(pth, 'RRLOG_ERROR')
  tcWarn = searchKeyInFiles(pth, 'RRLOG_WARNING')
  tcDebug = searchKeyInFiles(pth, 'RRLOG_DEBUG')
  tcInfo = searchKeyInFiles(pth, 'RRLOG_INFO')
  tcTrace = searchKeyInFiles(pth, 'RRLOG_TRACE')
  printlC('yellow', '', ', %s, %d, %d, %d, %d, %d'%(comp, tcError, tcWarn, tcDebug, tcInfo, tcTrace))
  return (tcError, tcWarn, tcDebug, tcInfo, tcTrace)
    
def calFolders():
  tcError = 0
  tcWarn = 0
  tcDebug = 0
  tcInfo = 0
  tcTrace = 0
  results = os.listdir(os.getcwd())
  comp = os.getcwd().split('\\')[-1]  
  for item in results:
    if os.path.isdir(item):
      rl = calFiles(os.getcwd(), item, '')
      tcError += rl[0]
      tcWarn += rl[1]
      tcDebug += rl[2]
      tcInfo += rl[3]
      tcTrace += rl[4]
  printlC('green', '', '%s, , %d, %d, %d, %d, %d'%(comp, tcError, tcWarn, tcDebug, tcInfo, tcTrace))
##########################################################
# 
##########################################################

def freqCounter(ipt):
  rDict = {}
  for item in ipt:
    if rDict.has_key(item):
      rDict[item] += 1
    else:
      rDict[item] = 1
  rList = []
  for i,j in rDict.items():
    rList.append((j,i))
  rList.sort(reverse = True)
  print rList

def freqCounter2(ipt):
  rDict = {}
  #for item in ipt:
  #  rDict.setdefault(item, 0)
  #  rDict[item] += 1
  for item in {}.fromkeys(list(ipt)):
    rDict[item] = len(ipt.split(item)) - 1

  #rList = sorted(['%d'%j+i for i,j in rDict.items()], reverse = True)
  #rList.sort(reverse = True)
  return ''.join(sorted(['%d'%j+i for i,j in rDict.items()], reverse = True))
       

def findAnagrams(iptList):
  rDict = {}
  for item in iptList:
    rDict.setdefault(freqCounter2(item), []).append(item)

  for item in rDict:
    print rDict[item]  
  
  
if __name__ == '__main__':
  #printlC('white', '', '[log] GIT assistant is started!')
  if len(sys.argv) == 2:
    cmdManager(sys.argv[1], None, None)
  elif len(sys.argv) == 3:
    cmdManager(sys.argv[1], sys.argv[2], None)
  elif len(sys.argv) >= 4:
    #printlC('yellow', '', 'arg3:(%s)'%sys.argv[3])
    cmdManager(sys.argv[1], sys.argv[2], sys.argv[3])  
  else:
    cmdManager(None, None, None)
  #printlC('white', '', '[log] GIT assistant is stopped!')
else:
  #checkGitEnv()
  ss = '07/09/2013  09:58 AM             1,619 AvpInfo.java'
  sl = ['abc', 'abd', 'bad', 'bda', 'bca', 'aaa', 'dba']
  s2 = '    //abc  dadfd  '
  s3 = 'string BstnUtil::timeString(time_t value)'
  r3 = '\w+\s+\w+::\w+\(.*\)'
  #findAnagrams(sl)
  print reCheck(s3, r3)
  #print freqCounter2(ss)
  #findAnagrams(sl)
  #findFile('AvpInfo.java')
  #compareModification('bmsc-mdf-cp')
  #calFolders()
  loopFiles()

  
   

  

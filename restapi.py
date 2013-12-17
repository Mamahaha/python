#!/usr/bin/env python
"""
restapi.py Learn REST API with Python script  
Usage: restapi.py [options] 

Options:
  -e --exer <number>            exercise number 
  -h                            this help

Mail bug reports and suggestion to : Larry Cai <larry.caiyu AT gmail.com>
"""

import getopt, sys, os, errno  
import getpass    
import requests
import json
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from HTMLParser import HTMLParser

# Reference:
# Understand REST API: http://www.restapitutorial.com/ 
# Requests python module: http://www.python-requests.org 
# Github developer API v3 http://developer.github.com/v3/
# Jenkins API https://wiki.jenkins-ci.org/display/JENKINS/Remote+access+API




class parselinks(HTMLParser):
  ''' HTML content parser.
      The result contains all data that matches <a href="/job/></a>
  '''
  def __init__(self):
      self.data=[]
      self.href=0
      self.linkname=''
      HTMLParser.__init__(self)
  def handle_starttag(self,tag,attrs):
      if tag =='a':
          for name,value in attrs:
              if name == 'href' and value.startswith('/job/'):
                  self.href=1
  def handle_data(self,data):
      if self.href:
          self.linkname+=data
  def handle_endtag(self,tag):
      if tag=='a':
          self.linkname=''.join(self.linkname.split())
          self.linkname=self.linkname.strip()
          if  self.linkname:
              self.data.append(self.linkname)
          self.linkname=''
          self.href=0
  def get_result(self):
      for value in self.data:
          print value
          
# exer1 : use curl to access http://httpbin.org/get
# exer2 : use requests module in python interactive module
#

def exer3():
    """
    learn requests module 
    task:
        get data from the server and print out response data like status_code, text, headers
    """
    server = "http://httpbin.org/get"
    r = requests.get(server)
    #print json.dumps(r.json(), indent = 2)
    print r.json()
    
# r = requests.get('https://github.com', verify=True)
# <Response [200]>
# r = requests.get('https://github.com', auth=HTTPBasicAuth(user,passwd))
#
def exer4():
    """
    learn https and authentication in requests
    learn real github example gist
    task:
       get your account's created date using authentication
    """
    server = "https://api.github.com"
    url = server + "/users"
    user = "mamahaha"
    passwd = getpass.getpass('Password:')
    print "checking ", url, "using user:", user
    r = requests.get(url, auth=HTTPBasicAuth(user,passwd))
    print r
    #print json.dumps(r.json(), indent = 2)
    
#>>> import json
#>>> url = 'https://api.github.com/some/endpoint'
#>>> payload = {'some': 'data'}
#>>> headers = {'content-type': 'application/json'}
#>>> r = requests.post(url, data=json.dumps(payload), headers=headers)
#
# check http://developer.github.com/v3/gists/#create-a-gist
#
def exer5():
    """
    learn POST method in requests
    learn create gist
    task: 
        create the gist for this script with name "restapi.py" and description "CodingWithMe sample"
    """
    server = "https://api.github.com"
    url = server + "/gists"
    user = "Mamahaha"
    passwd = getpass.getpass('Password:')

    local_file = "restapi.py"
    with open(local_file) as fh:
        mydata = fh.read()

    files = {
      "description": "rest api ",
      "public": "true",
      "user" : user,
      "files": {
        "file1.txt": {
          "content": mydata
        }
      }
    }
    r1 = requests.post(url, data=json.dumps(files), auth=HTTPBasicAuth(user,passwd))
    #print json.dumps(r1.json(), indent = 2)
    print r1.json()['url']
    #r2 = requests.get(r1.json()['url'], auth=HTTPBasicAuth(user,passwd))
    #print r2.json()['files']['file1.txt']['content']
    
def exer6():
    # this is bonus exercise
    # 7.1 Implement for all gist API
    #exer71()
    
    # 7.2 oauth to access github in python script
    #oauth_usage()
    
    # 7.3 Get all jenkins jobs in python script
    #get_jenkins_jobs()
    pass

# global variables
server = "https://api.github.com"
url = server + "/gists"
user = "Mamahaha"

# Implementation of gist api
def exer71():
  ''' gist api implementation
  '''
  gist_cmds = {
    'authentication' : lambda : gist_auth(),
    'list'           : lambda : gist_list(),
    'get'            : lambda : gist_get(),
    'create'         : lambda : gist_create(),
    'edit'           : lambda : gist_update(),
    'star'           : lambda : gist_star(),
    'unstar'         : lambda : gist_unstar(),
    'checkstar'      : lambda : gist_check_star(),
    'fork'           : lambda : gist_fork(),
    'delete'         : lambda : gist_delete(),      
  }
  print '========gist api list==========='
  for item in gist_cmds.keys():
    print item
  param = raw_input('\n$Choose a gist operation listed above: ')
  if param in gist_cmds.keys():
    gist_cmds[param]()
  else:
    print 'Error: Unsupported gist operation'

def gist_auth():
  None
def gist_list():
  global server
  global user
  passwd = getpass.getpass('$Password:')

  resp = {
    'user'     : lambda : requests.get(server + '/users/' + user + '/gists', auth=HTTPBasicAuth(user,passwd)),
    'all'      : lambda : requests.get(server + '/gists'),
    'public'   : lambda : requests.get(server + '/gists/public'),
    'starred'  : lambda : requests.get(server + '/gists/starred', auth=HTTPBasicAuth(user,passwd)),
  }
  print '========list type==========='
  for item in resp.keys():
    print item
  param = raw_input('\n$Choose a list type from above: ')
  if param in resp.keys():
    r = resp[param]()
    print r
    print json.dumps(r.json(), indent = 2)
  else:
    print 'Error: No such list type'
  
def gist_get():
  global server
  global user
  passwd = getpass.getpass('$Password:')
  id = raw_input('\n$Input the commit id that you want to get: ')
  r = requests.get(server + '/gists/' + id, auth=HTTPBasicAuth(user,passwd))
  print r
  print json.dumps(r.json(), indent = 2)

def gist_create():
  global server
  global user
  passwd = getpass.getpass('$Password:')
  url = server + "/gists"
  commit = {
    "description": "the description for this gist",
    "public": "true",
    "user" : user,
    "files": {
      "file1.txt": {
        "content": "ohyeah"
      }
    }
  }
  r = requests.post(url, data=json.dumps(commit), auth=HTTPBasicAuth(user,passwd))
  print r
  print json.dumps(r.json(), indent = 2)

def gist_update():
  global server
  global user
  passwd = getpass.getpass('$Password:')
  #id = raw_input('\n$Input the commit id that you want to get: ')
  id = 'b584f07661af97270500'
  url = server + "/gists/" + id
  print url
  commit = {
    "description": "the description for this gist",
    "files": {
      "file1.txt": {
        "content": "ohyeah again"
      },
      "file2.txt": {
        "content": "bye bye"
      }
    }
  }
  r = requests.patch(url, data=json.dumps(commit), auth=HTTPBasicAuth(user,passwd))
  print r
  print json.dumps(r.json(), indent = 2)
  
def gist_star():
  global server
  global user
  passwd = getpass.getpass('$Password:')
  #id = raw_input('\n$Input the commit id that you want to get: ')
  id = '9360b120fc97767b2959'
  url = server + "/gists/" + id + '/star'
  r = requests.put(url, auth=HTTPBasicAuth(user,passwd))
  print r
  
def gist_unstar():
  global server
  global user
  passwd = getpass.getpass('$Password:')
  #id = raw_input('\n$Input the commit id that you want to get: ')
  id = '9360b120fc97767b2959'
  url = server + "/gists/" + id + '/star'
  r = requests.delete(url, auth=HTTPBasicAuth(user,passwd))
  print r
  
def gist_check_star():
  global server
  global user
  passwd = getpass.getpass('$Password:')
  #id = raw_input('\n$Input the commit id that you want to get: ')
  id = '9360b120fc97767b2959'
  url = server + "/gists/" + id + '/star'
  r = requests.get(url, auth=HTTPBasicAuth(user,passwd))
  print r

def gist_fork():
  global server
  global user
  passwd = getpass.getpass('$Password:')
  #id = raw_input('\n$Input the commit id that you want to get: ')
  id = '9360b120fc97767b2959'
  url = server + "/gists/" + id + '/forks'
  r = requests.post(url, auth=HTTPBasicAuth(user,passwd))
  print r
  print json.dumps(r.json(), indent = 2)
  
def gist_delete():
  global server
  global user
  passwd = getpass.getpass('$Password:')
  #id = raw_input('\n$Input the commit id that you want to get: ')
  id = '9360b120fc97767b2959'
  url = server + "/gists/" + id
  r = requests.delete(url, auth=HTTPBasicAuth(user,passwd))
  print r
############end of exer71#####################
 
def oauth_usage():
  server = 'https://api.github.com'
  client_id = 'dd2593e8318bb93f713d'
  client_secret = '' #your own client_secret 
  personal_token = '' #your token created from <client_id, client_secret>
  auth_url = 'https://api.github.com/authorizations'
  token_postfix = 'x-oauth-basic'
  user = 'mamahaha'
  passwd = getpass.getpass('Password:')
  user_auth = HTTPBasicAuth(user, passwd)
  token_auth = HTTPBasicAuth(personal_token, token_postfix)
  
  #step1: list all client_id, token, id from authorize
  data1 = {
    'client_id'      : client_id,
    'redirect_uri'   : 'https://api.github.com/gists/b584f07661af97270500',
    'scope'          : ['repo'],
  }
  #r1 = requests.get(auth_url, auth=user_auth)
  #print r1
  #print json.dumps(r1.json(), indent = 2)
  #r1_client_id = r1.json()[4]['app']['client_id']
  #r1_token = r1.json()[4]['token']
  #r1_id = r1.json()[4]['id']
  #print r1_client_id, r1_token, r1_id
  
  #step2: get a single client_id and token according to a given id from authorize
  #r2 = requests.get(auth_url+'/4908958', auth=user_auth)
  #print r2
  #print json.dumps(r2.json(), indent = 2)
  
  #step3: create a new authorizations
  data3 = {
    'scopes'        : ['repo', 'gist', 'user'],
    'note'          : 'exer_token',
    'client_id'     : client_id,
    'client_secret' : client_secret
  }
  #r3 = requests.post(auth_url, data=json.dumps(data3), auth=user_auth)
  #print r3
  #print json.dumps(r3.json(), indent = 2)
  #r3_id = r1.json()['id']
  #r3_token = r1.json()['token']
  #r3_client_id = r1.json()['app']['client_id']
  
  #step4: get-or-create an authorization for a specific app'
  data4 = {
    'client_secret' : client_secret,
    'scope'         : ['repo'],
  }
  #r4 = requests.put(auth_url+'/clients/'+client_id, data=json.dumps(data4), auth=user_auth)
  #print r4
  #print json.dumps(r4.json(), indent = 2)

  #step5: update an existing authorization
  #TODO, use 'PATCH /authorizations/:id'
  
  #step6: delete an authorization
  #TODO, use 'DELETE /authorizations/:id'
  
  #step7: validate token
  #r7 = requests.get(server+'/applications/'+client_id+'/tokens/'+personal_token, auth=HTTPBasicAuth(client_id, client_secret))
  #print r7
  #print json.dumps(r7.json(), indent = 2)
  
  #step8: use a repo token to access repository
  #r8 = requests.get(server+'/users/Mamahaha/repos', auth=token_auth)
  #print r8
  #print json.dumps(r8.json(), indent = 2)

def get_jenkins_jobs():
  url1 = 'https://busstv-jenkins.sh.cn.ao.ericsson.se/view/BMC/view/BMC14A?verify=false'
  user = 'exuyufe'
  passwd = getpass.getpass('Password:')
  user_auth = HTTPBasicAuth(user, passwd)
  #this will return a html-format respone, and we need a html parser to get all jobs
  r = requests.get(url1, auth=user_auth, verify=False) 
  print r
  r2 = parselinks()
  data = r.content.decode('utf-8')
  r2.feed(data)
  r2.get_result()
  r2.close()
  
  
def enable_debug():
    import logging

    # These two lines enable debugging at httplib level (requests->urllib3->httplib)
    # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
    import httplib
    httplib.HTTPConnection.debuglevel = 1

    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig() 
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True           

def main(): 
    number = "3"
    try:
        cmdlineOptions, args= getopt.getopt(sys.argv[1:],'he:',["help","exer="])
    except getopt.GetoptError, e:
        raise "Error in a command-line option:\n\t" + str(e)

    for (optName,optValue) in cmdlineOptions:
        if  optName in ("-h","--help"):
            print __doc__
            sys.exit()
        elif optName in ("-e","--exer"):
            number = optValue
        else:
            errorHandler('Option %s not recognized' % optName)

    # mostly you don't need to understand below, focus on exercise 
    # Get it from globals and invoke `exerx()` method directly
    method_name = "exer" + number
    method_list = globals()
    if method_name in method_list:
        method_list[method_name]()
    else:
        print "the exericse %s is not ready, please create method `exer%s` directly" % (number, number )

if __name__ == "__main__": 
  main()
else:
  #gist_create()
  #gist_star()
  #gist_check_star()
  #gist_fork()
  #get_jenkins_jobs()
  #flask_auth()
  #exer5()
  pass

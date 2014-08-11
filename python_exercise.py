#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Python exercises
Usage: python_exercise.py [Options]

Options:
  -n --number <number>            exercise number 

Mail bug reports and suggestion to : Led Xu <led.xu@ericsson.com>
'''

import argparse as AP

# ==============Exercise 1==============
def ex1():
  ''' 
  hello world
  task:
    1.print out 'Hey Python! I'm coming!'
  '''
  #----Fill your codes below---
  print 'Hey Python! I\'m coming!' 
  #----------------------------
  None

# ==============Exercise 2==============
def ex2():
  '''
  string operations
  task:
    1. create a new string 'bd23' by cutting & merging s1 and s2
  '''
  s1 = 'abcd'
  s2 = '1234'
  #----Fill your codes below---
  print s1[1::2] + s2[1:3]  
  #----------------------------
  #print ''.join([i for i in s1[1::2]] + [j for j in s2[1:3]])


# ==============Exercise 3==============
def ex3():
  '''
  control flow
  task:
    1. count how many 'b' in string s by looping string and checking each character
  '''
  s = 'vadfdfbblbldafbdfkdbaadbb'
  #----Fill your codes below---
  count = 0
  for i in s:
    if i == 'b':
      count += 1
  print '%s has %d b' %(s, count)
  #----------------------------
  #print s.count('b')
  
  
# ==============Exercise 4==============
def ex4():
  '''
  list operations
  task:
    1. create a new list with numbers that can be divided by 3 in list s
  '''
  s = range(2, 200, 5)
  #----Fill your codes below---
  s2 = []
  for i in s:
    if i % 3 == 0:
      s2.append(i)
  print s2  
  #----------------------------
  #print [i for i in s if i%3==0]

# ==============Exercise 5==============
def ex5():
  '''
  dictionary & set operations
  task:
    1.add a new phone number 'business' : '021-43215' in dict s
    2.remove duplicated friends from dict s
  '''
  s = {
    'name'  : 'Led',
    'phone' : {'mobile' : '13612345',
               'home'  : '021-56789'
              },
    'friends': ['Tom', 'Jerry', 'Tom', 'Micky', 'Micky'],
  }
  #----Fill your codes below---
  s['phone']['business'] = '021-43215'
  s['friends'] = list(set(s['friends']))
  print s
  #----------------------------

# ==============Exercise 6==============
#----Fill your codes below---
def fib(n):
  ls = [0, 1]
  for i in range(2,n):
    ls.append(ls[i-1]+ls[i-2])
  return ls
#----------------------------
  
def ex6():
  '''
  function definition
  taks:
    1.define a recursive function fib(a, b, n)  -> 0 1 1 2 3 5 8
    2.print Fibnacci series up to n when calling it  
  '''
  print fib(200)
  
# ==============Exercise 7==============
import json
import requests

def ex7():
  '''
  parse JSON data
  task:
    1.get the value of 'origin' from json_data
    2.get the value of 'Connection' from json_data
  '''
  server = "http://httpbin.org/get"
  r = requests.get(server)
  json_data = r.json()
  #----Fill your codes below---
  
  #----------------------------
  
# ==============Exercise 8 (bonus)==============
def curry_a(a):
  def curry_b(b):
    def curry_c(c, d, e):
      print a, b, c, d, e
    return curry_c
  return curry_b
      
def ex8():
  '''
  higher order functions
  task:
    1.use 'lambda' to double the values of all items in list s1
    2.use 'filter' to rewrite ex4
    3.use 'map' to double the values of all items in list s3
    4.use 'reduce' to add all items in list s4
    5.currying example
  '''
  #----lambda-----------------
  s1 = [1,2,3,4,5]
  #s1 = [(lambda x : x*2)(a) for a in s1]
  #----filter-------------
  s2 = range(2, 200, 5)
  #s2 = filter(lambda x:x%3==0, s2)
  #----map-------------
  s3 = [1,2,3,[4,5,6]]
  #s3 = map(lambda x:x*2, s3)
  #----reduce-------------
  s4 = [1,2,3,4]
  #result = reduce(lambda x,y:x+y, s4)
  #----currying-------------
  c1 = curry_a(1)
  #c2 = c1(2)
  #c2(3, 4, 5)


# ==============Exercise 9 (bonus)==============
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
      print '[Error]: Failed to run command <%s>' %cmd
      raise 
  
def ex9():
  '''
  use run_cmd() to access your git repository
  task:
    1.git status
    2.git pull
    3.git add
    4.git commit
    5.git push for review
  '''
  #----Fill your codes below---
  
  #----------------------------
  pass
  
  
#===============Basic Functions=========
def run_exercise(exer_number):
  func_name = 'ex%d()'%(exer_number)
  #printc('white', 'blue', '#--Exercise %d start'%exer_number)
  print '\033[0m#--Exercise %d start\033[1m'%exer_number
  exec(func_name)
  print '\033[0m#--Exercise %d stop'%exer_number
  #printc('white', 'blue', '#--Exercise %d stop'%exer_number)


#===============colorful output=========
bgc_dict = {}
fgc_dict = {}

fgc_dict['red']     = 31
fgc_dict['green']   = 32
fgc_dict['yellow']   = 33
fgc_dict['blue']    = 34
fgc_dict['purple']  = 35
fgc_dict['white']   = 37
fgc_dict['black']   = 30

bgc_dict['red']     = 41
bgc_dict['green']   = 42
bgc_dict['yellow']   = 43
bgc_dict['blue']    = 44
bgc_dict['purple']  = 45
bgc_dict['white']   = 47
bgc_dict['black']   = 49

def printc(bgc,fgc, str):
  print '\033[5m\033[%d;%dm%s\033[0m' %(bgc_dict[bgc], fgc_dict[fgc], str)

# ==============Main====================
if __name__ == '__main__':
  try:
    parser = AP.ArgumentParser()
    parser.add_argument('-n', '--number', nargs="+", type=int)
    #parser.add_argument('-h', '--help')
    arg_dict = parser.parse_args().__dict__
    if arg_dict['number'] != None:
      run_exercise(arg_dict['number'][0])
    else:
      print __doc__
  except Exception,e:
    print e 

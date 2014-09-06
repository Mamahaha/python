#!/usr/bin/python
#-*-coding:utf-8 -*-
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
  point:
    1. usage of print
    2. usage of escape character \
    3. difference of single_quotes, double_quotes, triple_quotes
  task:
    1.print out 'Hey Python, I'm xx'
  '''
  #----Fill your codes below---
  
  #----------------------------
  #print 'Hey Python, I\'m %s, code %d!' %('华安', 9527)
  pass

# ==============Exercise 2==============
def ex2():
  '''
  variable types
  point:
    1. variable assignment (=, +=, -=, *=, /=, %=, **=, //=)
    2. basic arthmetic operators (+, -, *, /, %, **, //)
    3. string operations (slice and concatenation)
    4. data type conversion (int(x), long(x), float(x), str(x), eval(str), tuple(s), set(s), dict(s), ord(x), hex(x))
    5. #optional# check data type (type(var))
    6. #optional# check attributes of a variable (dir(var))
  task:
    1. create a new string 'bd23' by cutting & merging str1 and int2
  '''
  int1 = 100
  float1 = float2 = 100.4
  str1, int2 = 'abcd', 1234
  #----Fill your codes below---
  
  #----------------------------
  #str3 = s1[1::2] + s2[1:3]  
  str3 = ''.join([i for i in str1[1::2]] + [j for j in str(int2)[1:3]])
  print str3


# ==============Exercise 3==============
def ex3():
  '''
  control flow
  point:
    1. comparison operators(==, !=, <>, >, >=, <=)
    2. logical operators (and, or, not, in, is, is not)
    3. if : elif : else
    4. for :
    5. for item in items:
    6. while :
    7. do: while
    8. #optional# get the address of a variable (id(var))
  task:
    1. count how many 'b' in string s by looping string and checking each character
  '''
  s = 'vadfdfbblbldafbdfkdbaadbb'
  #----Fill your codes below---
  count = 0
  for i in s:
    if not i != 'b':
      count += 1
  print '%s has %d b' %(s, count)
  #----------------------------
  #print s.count('b')
 

# ==============Exercise 4==============
def ex4():
  '''
  list & tuple operations
  point:
    1. define an empty list  (s=[])
    2. define an empty tuple (s=())
    3. update an item in list   (items[index] = new_value)
    4. add a new item into list (append(item))
    5. remove an item from list (del items[index]) (items.remove(item))
    6. #optional# range() and xrange()
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
  points:
    1. define an empty dict (s={})
    2. dict operations(add, update, remove, search) 
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
  points:
    1. input parameters(f1(a1, a2), f2(a1, a2=1)
    2. parameter passing mode (for mutable objects and immutable objects: passing by reference)
    3. the difference of variable and object
    3. output parameters 
  taks:
    1.define a recursive function fib(a, b, n)  -> 0 1 1 2 3 5 8
    2.print Fibnacci series up to n when calling it  
  '''
  print fib(20)
  
# ==============Exercise 7==============
import json
import requests

def ex7():
  '''
  parse JSON data
  point:
    1. get to know json
    2. get to know restful API
    3. #optional# use curl command to check the output (curl -i -X GET http://httpbin.org/get)
  task:
    1.get the value of 'origin' from json_data
    2.get the value of 'Connection' from json_data
  '''
  server = "http://httpbin.org/get"
  r = requests.get(server)
  json_data = r.json()
  #print json_data
  #----Fill your codes below---
  
  #----------------------------
  #print json_data['origin']
  #print json_data['headers']['Connection']
  
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
  print '\033[0m#--Exercise %d start\033[1m\033[7m'%exer_number
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

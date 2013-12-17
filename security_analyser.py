#!/usr/bin/python

import urllib
import urllib2
import time 
import re

urlString = 'http://hq.sinajs.cn/list=sz150099,sz150098,sz150060,sz150059,sz150031,sz150030,sz150029,sz150028,sz150023,sz150022,sz150019,sz150018,sz150013,sz150012,sz150101,sz150100,sz150086,sz150085,sz150052,sz150051,sz150097,sz150096'
urlString2 = 'http://hq.sinajs.cn/list=sz399906,sz399944,sh000971,sz399905,sz399001,sz399330,sz399903,sh000805,sz399005,sz399300,sz399979'


def save2File(filePath, content):
  try:
    fh = open(filePath, 'w')
    fh.write(content)
    fh.close()
    return True
  except Exception, ex:
    return False
  
def loader(url_string): 

### for cbc env   ####################
  proxy_support = urllib2.ProxyHandler({'http':'http://www-proxy.ao.ericsson.se:8080'})
  opener = urllib2.build_opener(proxy_support)
  urllib2.install_opener(opener)
######################################

  resp = urllib2.urlopen(url_string).read()
  print resp
  
  flag = save2File('data.txt', resp)
  while not flag:
    print '[Error] Failed to save file data.txt'
    time.sleep(5)
    flag = save2File('data.txt', resp)

def loader2(): 

### for cbc env   ####################
  proxy_support = urllib2.ProxyHandler({'http':'http://www-proxy.ao.ericsson.se:8080'})
  opener = urllib2.build_opener(proxy_support)
  urllib2.install_opener(opener)
######################################

  resp = urllib2.urlopen(urlString2).read()
  print resp

  flag = save2File('data_benchmark.txt', resp)
  while not flag:
    print '[Error] Failed to save file data_benchmark.txt'
    time.sleep(5)
    flag = save2File('data_benchmark.txt', resp)

def load_data(url_string):
#Only for company start#########
  proxy_support = urllib2.ProxyHandler({'http':'http://www-proxy.ao.ericsson.se:8080'})
  opener = urllib2.build_opener(proxy_support)
  urllib2.install_opener(opener)
#Only for company end#########
  resp = urllib2.urlopen(url_string).read()
  #print resp.strip()
  return resp.strip()


MAX_INVESTMENT = 200000
input_list = []
def parse_input(fp):
  fh = open(fp)
  lines = fh.readlines()
  fh.close()
  
  rr = re.compile('(\t| )+')
  for line in lines:
    new_line = line.strip()
    if new_line.startswith('#') or new_line == '':
      continue
    items = rr.split(new_line)
    n_l = [i for i in items if i != ' ' and i != '\t']
    if len(n_l) != 6:
      print 'error line:', n_l
      continue
    input_list.append(n_l)

def parse_all():
  for i in input_list:
    parse_data(i)

  
def parse_data(line):
  a = parse_AB(line[0])
  b = parse_AB(line[1])
  parent = parse_parent(line[2])
  benchmark = parse_benchmark(line[3])
  a_weight = line[4]
  b_weight = line[5]
  #print 'a:',a
  #print 'b:',b
  #print 'ben:',benchmark
  roi = process_ROI(float(a[1]), float(b[1]), float(parent), float(benchmark[0]), float(benchmark[1]), float(a_weight), float(b_weight))
  (buy_percentage_a, buy_percentage_b) = process_impact_degree(float(a[1]), float(a[0]), float(b[1]), float(b[0]), float(a_weight), float(b_weight))
  result = 'ROI: %5.2f%% A:%s,%s,%s,%5.2f%% B:%s,%s,%s,%5.2f%%' %(roi * 100, line[0], a[1], a[0], buy_percentage_a * 100, line[1], b[1], b[0], buy_percentage_b * 100)
  if roi in unsorted_result.keys():
    unsorted_result[roi].append(result)
  else:
    unsorted_result[roi] = [result]

unsorted_result = {}
def print_sorted_result():
  keys = unsorted_result.keys()
  keys.sort()
  sorted_result = [unsorted_result[key] for key in keys]
  for i in sorted_result:
    for j in i:
      print j
      
def process_ROI(a_price, b_price, parent_lastnight, benchmark_lastnight, benchmark_now, a_weight, b_weight):
  if a_price == 0.0 or b_price == 0.0:
    return 0.0
  benchmark_change = (benchmark_now - benchmark_lastnight) / benchmark_lastnight
  parent_now = parent_lastnight * (1 + benchmark_change)
  a_now = a_price * a_weight
  b_now = b_price * b_weight
  roi = ( a_now + b_now ) / parent_now  - 1
  return roi

def process_impact_degree(a_price, a_amount, b_price, b_amount, a_weight, b_weight):
  if a_price == 0.0 or b_price == 0.0 or a_amount == 0.0 or b_amount == 0.0:
    return (0.0, 0.0)
  total = a_price * a_weight + b_price * b_weight
  max_investment_a = MAX_INVESTMENT * a_price * a_weight / total
  max_investment_b = MAX_INVESTMENT * b_price * b_weight / total
  max_investment_amount_a = max_investment_a / a_price
  max_investment_amount_b = max_investment_b / b_price  
  buy_percentage_a =   max_investment_amount_a / a_amount
  buy_percentage_b =   max_investment_amount_b / b_amount
  #print (buy_percentage_a, buy_percentage_b)
  return (buy_percentage_a, buy_percentage_b)
  
def parse_AB(s):
  url_string = 'http://hq.sinajs.cn/list=sz%s' %s
  resp = load_data(url_string)
  return parse_resp_AB(resp)
  
  
def parse_parent(s):
  url_string = 'http://hq.sinajs.cn/list=f_%s' %s
  resp = load_data(url_string)
  return parse_resp_parent(resp)

def parse_benchmark(s):
  url_string = 'http://hq.sinajs.cn/list=%s' %s
  resp = load_data(url_string)
  return parse_resp_benchmark(resp)
  
  
def parse_resp_AB(resp):
  r1 = resp.split('=')[1].split('"')[1].split(',')
  r2 = r1[len(r1)-13:-1]
  #print r2
  return r2
  
def parse_resp_parent(resp):
  r1 = resp.split(',')[1]
  #print r1
  return r1

def parse_resp_benchmark(resp):
  r1 = resp.split(',')[2:4]
  #print r1
  return r1
  
config_dict = {}
def load_config(fp):
  fh = open(fp)
  lines = fh.readlines()
  fh.close()
  
  for line in lines:
    if not '=' in line:
      continue
    items = line.split('=')
    config_dict[items[0].strip()] = items[1].strip()
  #print config_dict

def loop_run():
  load_config('C:\\personal\\sys_env\\data.cfg')
  parse_input(config_dict['input_file'])
  while True:    
    parse_all()
    print_sorted_result()
    time.sleep(int(config_dict['interval']))

  
if __name__ == '__main__':  

### while from 9:30~15:00  start ####################
  while True:
    loader(url_string)
    time.sleep( 5 ) 
    loader2()
    time.sleep( 5 ) 

  

  
### while from 9:30~15:00   end  ####################

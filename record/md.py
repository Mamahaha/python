#!/usr/bin/python
#-*-coding:utf-8 -*-
'''
Created on Aug 26, 2016

@author: led
'''

import xml.etree.ElementTree as ET


MODULE_FOLDER = '/home/led/gh/python/record'
DB_NAME = 'mem'
module_list = []

import subprocess
def run_cmd(cmd):
    try:
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (result, err) = p.communicate(cmd)
        return (result, err)
    except Exception, ex:
        print '[Error]: Failed to run command <%s> with error <%s>' %(cmd, ex)
        
  
import psycopg2
def init_db(db):
    run_cmd('%s/init_db.sh %s' %(MODULE_FOLDER, DB_NAME))
    
def init_tables(db):
    conn = psycopg2.connect(database=db)
    cur = conn.cursor()    
    
    for file_name in module_list:
        module = file_name.split('.')[0]
        try:
            cur.execute('CREATE TABLE %s' %(module) + ''' 
                        (NAME TEXT PRIMARY KEY NOT NULL,
                         VERSION TEXT NOT NULL,
                         TYPE TEXT,
                         DESCRIPTION TEXT,
                         CONTENT TEXT
                         );''')
        except Exception:
            pass
            #print 'Table <%s> already exists in database.' %(module)            
    conn.commit()
    conn.close()

def adjust_content(old_ct):
    new_ct = old_ct.replace('\'', '\'\'')
    return new_ct

def parse_feature(feature):
    name = feature.attrib['name']
    ver = 'common'
    des = feature.find('description').text
    tp = 'text'
    if feature.attrib.has_key('version'):
        ver = feature.attrib['version']
    if ver == None or ver == '':
        ver = 'common'
    if des == None or des == '':
        des = 'N/A'
    if feature.attrib.has_key('type'):
        tp = feature.attrib['type']
    ct = feature.find('content').text
    return (name, ver, tp, des, ct)
        
def fill_db(db):
    conn = psycopg2.connect(database=db)
    cur = conn.cursor()
    
    for file_name in module_list:
        module = file_name.split('.')[0]
        tree = ET.ElementTree(file='%s/data/%s' %(MODULE_FOLDER, file_name))
        root = tree.getroot()
        features = root.findall('./feature')
        for feature in features:
            if feature.attrib['name'] == None or feature.attrib['name'] == '':
                continue
            (name, ver, tp, des, ct) = parse_feature(feature)
            sql_cmd = ('INSERT INTO %s(NAME, VERSION, TYPE, DESCRIPTION, CONTENT) VALUES(\'%s\', \'%s\', \'%s\', \'%s\', \'%s\');'
                        %(module, name, ver, tp, des, adjust_content(ct)))
            try:
                cur.execute(sql_cmd)
            except Exception, ex:
                print 'ERROR when inserting record:', module, name, ver, tp, des, ct, ex
                    
    conn.commit()
    conn.close()
    
def clear_db(db):
    conn = psycopg2.connect(database=db)
    cur = conn.cursor()
    for file_name in module_list:
        module = file_name.split('.')[0]
        sql_cmd = 'DELETE FROM %s;' %(module)
        print 'sql_cmd:', sql_cmd
        try:
            cur.execute(sql_cmd)
        except Exception:
            print 'ERROR when clearing table:', module
    conn.commit()
    conn.close()

def list_module_db(db):
    conn = psycopg2.connect(database=db)
    cur = conn.cursor()
    sql_cmd = 'SELECT tablename FROM pg_tables WHERE tablename NOT LIKE \'pg%\' AND tablename NOT LIKE \'sql_%\';'
    cur.execute(sql_cmd)
    rows = cur.fetchall()
    for row in rows:
        printc('black', 'yellow', '* %s' %(row[0]))
    conn.close()

def get_module(m_prefix):
    tmp_prefix = m_prefix.strip().lower()
    target_modules = [i.split('.')[0] for i in module_list if i.startswith(tmp_prefix)]
    
    if len(target_modules) == 0:
        log_error_and_exit('No such component: %s' %m_prefix)
    
    if len(target_modules) > 1:
        log_error_and_exit('More than one module has the prefix: <%s>. Please input a more accurate module name' %m_prefix)
    return target_modules[0]
    
def list_feature_db(db, m_prefix):
    conn = psycopg2.connect(database=db)
    cur = conn.cursor()
    sql_cmd = 'SELECT name, version, description FROM %s;' %(get_module(m_prefix))
    cur.execute(sql_cmd)
    rows = cur.fetchall()
    conn.close()
    
    for row in rows:
        line = '* ' + row[0].ljust(20) + ' | ' + row[1].ljust(7) + ' | ' + row[2]
        printc('black', 'yellow', line)
    
    
def show_feature_db(db, m_prefix, f_prefix):
    conn = psycopg2.connect(database=db)
    cur = conn.cursor()
    sql_cmd = 'SELECT name, type, content FROM %s WHERE name LIKE \'%s%%\';' %(get_module(m_prefix), f_prefix)
    cur.execute(sql_cmd)
    rows = cur.fetchall()
    conn.close()
    
    for row in rows:
        printc('blue', 'white', '===============%s================' %(row[0]))
        show_content(row[2], row[1])
    
    
import sys
def log_error_and_exit(msg):
    printc('black', 'red', 'ERROR: %s\n' %msg)
    sys.exit()

import os
def init():
    global module_list
    for root, dirs, files in os.walk('%s/data' %(MODULE_FOLDER)):
        module_list = files

def show_content(content, content_type):
    if content_type == 'code':
        lines = content.split('\n')    
        for line in lines:
            printc('black', 'green', '%s' %(line))
    elif content_type == 'text':
        lines = content.strip().split('\n')
        for line in lines:
            ll = line.strip()
            if ll.startswith('----'):
                printc('black', 'yellow', '%s' %(ll))
            else:
                printc('black', 'green', '%s' %(ll))

        print ''


#===============colorful output=========
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

def show_usage():
    printc('black', 'blue', '** 6 usages: **')
    printc('black', 'yellow', '1. Show all modules')
    printc('black', 'deep_g', '   md')
    printc('black', 'yellow', '2. Update database')
    printc('black', 'deep_g', '   md a')
    printc('black', 'yellow', '3. Clean database')
    printc('black', 'deep_g', '   md d')
    printc('black', 'yellow', '4. Show all modules')
    printc('black', 'deep_g', '   md l')
    printc('black', 'yellow', '5. Show all features in a module')
    printc('black', 'deep_g', '   md <module>')
    printc('black', 'yellow', '6. Show the content of a feature')
    printc('black', 'deep_g', '   md <module> <feature>')
    
if __name__ == '__main__':
    init()
    if len(sys.argv) == 1:
        show_usage()
    elif len(sys.argv) == 2:
        if sys.argv[1] == 'a':
            init_db(DB_NAME)
            init_tables(DB_NAME)
            clear_db(DB_NAME)
            fill_db(DB_NAME)
        elif sys.argv[1] == 'd':
            clear_db(DB_NAME)
        elif sys.argv[1] == 'l':
            list_module_db(DB_NAME)
        else:
            list_feature_db(DB_NAME, sys.argv[1])
    elif len(sys.argv) == 3: 
        show_feature_db(DB_NAME, sys.argv[1], sys.argv[2])
    else:
        show_usage() 
    
#!/usr/bin/python
'''
# This is a h2 database client.
# Before using it, make sure below resources are ready:
#   1. Install h2 database
#       Url: http://www.h2database.com/html/main.html
#       Install: ./build.sh compile
#   2. Start h2 server.
#       Port 8082 is open
#   3. Install JayDeBeApi
#       Url: https://pypi.python.org/pypi/JayDeBeApi/#usage
#       Install: yum install python-devel.x86_64
#                pip install JayDeBeApi
'''


import jaydebeapi as J
  

db_name = 'led'
db_user = 'led'
db_pswd = 'bmc'
db_table = 'nodes'

def run_sql(cmd, needResult):
    conn = J.connect('org.h2.Driver', ['jdbc:h2:~/%s;AUTOCOMMIT=ON' %(db_name), db_user, db_pswd], '/path/to/hsqldb.jar',)
    curs = conn.cursor()
    print 'function run_sql command:', cmd
    curs.execute(cmd)
    if needResult:
        return curs.fetchall()

def add_records(args):
    cmd = "INSERT INTO nodes VALUES('201', '10.175.183.201', 'root', 'embms1234', 'BMC_15A', 'BMC 15A HA SC1')"
    #cmd = "INSERT INTO nodes VALUES('%s', '%s', '%s', '%s', '%s', '%s')" %(name, ip, user, pwd, group, desc)
    run_sql(cmd, False)
    print 'after insert:', run_sql("select * from nodes", True)

def add_record(name, ip, user, pwd, group, desc):
    cmd = "INSERT INTO nodes VALUES('201', '10.175.183.201', 'root', 'embms1234', 'BMC_15A', 'BMC 15A HA SC1')"
    #cmd = "INSERT INTO nodes VALUES('%s', '%s', '%s', '%s', '%s', '%s')" %(name, ip, user, pwd, group, desc)
    run_sql(cmd, False)
    print 'after insert:', run_sql("select * from nodes", True) 

def get_record(name):
    #cmd = "select usr, ip, pwd from nodes where name='%s'" %(name)
    cmd = "select * from nodes"
    result = run_sql(cmd, True)
    print 'get_record:', result

class h2_database:
    
    conn = None
    def __init__(self, db_name, user, pwd):
        if self.conn == None:
            self.conn = J.connect('org.h2.Driver', ['jdbc:h2:~/%s' %(db_name), user, pwd], '/path/to/hsqldb.jar',)
    
    def run_sql(self, cmd, needResult):
        if self.conn != None:
            curs = self.conn.cursor()
            print 'run_sql command:', cmd
            curs.execute(cmd)
            if needResult:
                return curs.fetchall()
        else:
            print '[ERROR]: DB cannot be connected'

class led_data_operator:
    '''
    # This is used to operator led database
    # Before using it, make sure database led is already created.
    '''
    #h2_instance = None
    def __init__(self):
        #self.h2_instance = h2_database('led', 'led', 'bmc')
        pass

    def create_table(self, cmd):
        cmd = ''' 
                'create table nodes'    
                '("CUST_ID" INTEGER not null,'  
                ' "NAME" VARCHAR not null,' 
                ' primary key ("CUST_ID"))'
              '''
        run_sql(cmd, False)
    
    def list_all(self):
        None

    def list_group(self):
        None

    def add_record(self, name, ip, user, pwd, group, desc):
        #cmd = "INSERT INTO nodes VALUES('201', '10.175.183.201', 'root', 'embms1234', 'BMC_15A', 'BMC 15A HA SC1')"
        cmd = "INSERT INTO nodes VALUES('201', '10.175.183.201', 'root', 'embms1234', 'BMC_15A', 'BMC 15A HA SC1')"
        #cmd = "INSERT INTO nodes VALUES('%s', '%s', '%s', '%s', '%s', '%s')" %(name, ip, user, pwd, group, desc)
        #self.h2_instance.run_sql(cmd, False)
        run_sql(cmd, False)

    def update_record(self, name, ip, user, pwd, group, desc):
        result = self.get_record(name)
        if len(result) == 0:
            print 'No such record exists:', name
            self.add_record(name, ip, user, pwd, group, desc)
        else:
            print 'The record already exists:', result
            cmd = "UPDATE nodes SET ip='%s', usr='%s', pwd='%s', grp='%s', desc='%s' WHERE name='%s'" %(ip, user, pwd, group, desc, name)
            run_sql(cmd, False)


    def get_record(self, name):
        cmd = "select usr, ip, pwd from nodes where name='%s'" %(name)
        result = run_sql(cmd, True)
        #print 'led_data_operator get_record:', result
        return result

    def delete_record(self, name):
        cmd = "delete from nodes where name='%s'" %(name)
        result = run_sql(cmd, False)


##################################################
#   Function Area
##################################################

def update_record(p):
    obj = led_data_operator()
    if len(p) != 8:
        print '[ERROR]: update_record wrong paramater number:', p
    else:
        print 'update_record:', p
        # key, ip, user, pwd, group, desc
        #obj.update_record(p[2], p[3], p[4], p[5], p[6], p[7])
        add_record(p[2], p[3], p[4], p[5], p[6], p[7])

def get_records(p):
    obj = led_data_operator()
    if len(p) != 3:
        print '[ERROR]: get_record wrong paramater number:', p
    else:
        result = get_record(p[2])
        print 'get_record:', result
        if result == None or len(result) == 0:
            print '[ERROR]: get_record no matched record exists:', p[2]
        else:
            (user, ip, pwd) = result[0]
            print 'get_record:', (user, ip, pwd)
            #return 'ssh %s@%s' %(user, ip)


def delete_record(p):
    obj = led_data_operator()
    if len(p) != 3:
        print '[ERROR]: delete_record wrong paramater number:', p
    else:
        print 'delete_record:', p
        obj.delete_record(p[2])

def test_sql():
    pass
    #run_sql("delete from nodes where name='201'", False)
    #print 'before insert:', run_sql("select * from nodes", True)

    #run_sql("INSERT INTO nodes VALUES('201', '10.175.183.201', 'root', 'embms1234', 'BMC_15A', 'BMC 15A HA SC1')", False)
    #print 'after insert:', run_sql("select * from nodes", True)

    #run_sql("delete from nodes where name='201'", False)
    #print 'after delete:', run_sql("select * from nodes", True)

def test_sql1(): 
    conn = J.connect('org.h2.Driver', ['jdbc:h2:~/led;AUTOCOMMIT=OFF', 'led', 'bmc'], '/path/to/hsqldb.jar',)
    curs = conn.cursor()
    curs.execute("INSERT INTO nodes VALUES('201', '10.175.183.201', 'root', 'embms1234', 'BMC_15A', 'BMC 15A HA SC1')")
    curs.execute("select * from nodes")
    print curs.fetchall()

def test_sql2(): 
    conn = J.connect('org.h2.Driver', ['jdbc:h2:~/led', 'led', 'bmc'], '/path/to/hsqldb.jar',)
    curs = conn.cursor()
    curs.execute("select * from nodes")
    print curs.fetchall()

import sys
if __name__ != '__main__':
     
    operations = {
        'a' : lambda : add_records(sys.argv),
        'u' : lambda : update_record(sys.argv),
        'g' : lambda : get_records(sys.argv),
        'd' : lambda : delete_record(sys.argv),    
    }

    if len(sys.argv) > 1 and sys.argv[1] in operations.keys():
        operations[sys.argv[1]]()
        
    else:
        print 'Usage:'
        print '  ./h2_access.py u name ip user pwd group desc'
        print '  ./h2_access.py g name'
        print '  ./h2_access.py d name\n'
else:
    if sys.argv[1] == '1':
        test_sql1()
    else:
        test_sql2()

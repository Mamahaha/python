#!/usr/bin/python
'''
# This is a h2 database client.
# Before using it, make sure below resources are ready:
#   1. Install h2 database
#       Url: http://www.h2database.com/html/main.html
#       Install: ./build.sh compile
#   2. Install JayDeBeApi
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
    conn = J.connect('org.h2.Driver', ['jdbc:h2:~/%s' %(db_name), db_user, db_pswd], '/path/to/hsqldb.jar',)
    curs = conn.cursor()
    #print 'function run_sql command:', cmd
    curs.execute(cmd)
    if needResult:
        result =  curs.fetchall()
        conn.close()
        return result
    else:
        conn.commit()
        conn.close()
    

########################################
#   Operations on TABLE 'nodes'
########################################

class nodes_class:
    '''
        This class is used for operating table 'nodes' in DB 'led'.
        Before using it, make sure database 'led' is already created.
        Table 'nodes' structure:
        | name(PK) | ip | usr | pwd | grp | desc |
    '''
    
    def __init__(self):
        None

    def create_table(self):
        cmd = "CREATE TABLE %s(%s VARCHAR(100) PRIMARY KEY, %s VARCHAR(100), %s VARCHAR(100), %s VARCHAR(100), %s VARCHAR(100), %s VARCHAR(255))" %(db_table, 'name', 'ip', 'usr', 'pwd', 'grp', 'desc')
        run_sql(cmd, False)

    def drop_table(self):
        cmd = "DROP TABLE %s" %(db_table)
        run_sql(cmd, False)

    def add_record(self, name, ip, user, pwd, group, desc):
        cmd = "INSERT INTO %s VALUES('%s', '%s', '%s', '%s', '%s', '%s')" %(db_table, name, ip, user, pwd, group, desc)
        run_sql(cmd, False)
        #print 'after add:', run_sql("select * from %s" %(db_table), True) 

    def update_record(self, name, ip, user, pwd, group, desc):
        result = self.get_record(name)
        if len(result) == 0:
            print 'No such record exists:', name, '. Will add a new record'
            self.add_record(name, ip, user, pwd, group, desc)
        else:
            print 'The record already exists:', result
            cmd = "UPDATE %s SET ip='%s', usr='%s', pwd='%s', grp='%s', desc='%s' WHERE name='%s'" %(db_table, ip, user, pwd, group, desc, name)
            run_sql(cmd, False)
        #print 'after add:', run_sql("select * from %s" %(db_table), True)

    def get_record(self, name):
        cmd = "select usr, ip, pwd from %s where name='%s'" %(db_table, name)
        result = run_sql(cmd, True)
        #print 'get_record:', result
        return result

    def delete_record(self, name):
        cmd = "delete from %s where name='%s'" %(db_table, name)
        run_sql(cmd, False)
        #print 'after add:', run_sql("select * from %s" %(db_table), True)


##################################################
#   Function Area
##################################################
nodes_instance = nodes_class()

def print_usage():
    print 'Usage:'
    print '  ./h2_access.py u name ip user pwd group desc'
    print '  ./h2_access.py g name'
    print '  ./h2_access.py d name\n'

def update_record(p):
    if len(p) != 8:
        print_usage()
    else:
        print 'update_record:', p
        # key, ip, user, pwd, group, desc
        nodes_instance.update_record(p[2], p[3], p[4], p[5], p[6], p[7])        

def get_records(p):
    if len(p) != 3:
        print_usage()
    else:
        result = nodes_instance.get_record(p[2])
        if result == None or len(result) == 0:
            print '[ERROR]: get_record no matched record exists:', p[2]
        else:
            (user, ip, pwd) = result[0]
            print 'get_record:', (user, ip, pwd)
            #return 'ssh %s@%s' %(user, ip)

def delete_record(p):
    if len(p) != 3:
        print_usage()
    else:
        nodes_instance.delete_record(p[2])

##################################################
#   Test Area
##################################################
def test_sql():
    pass
    #run_sql("delete from nodes where name='201'", False)
    #print 'before insert:', run_sql("select * from nodes", True)

    run_sql("INSERT INTO nodes VALUES('201', '10.175.183.201', 'root', 'embms1234', 'BMC_15A', 'BMC 15A HA SC1')", False)
    print 'after insert:', run_sql("select * from nodes", True)

    #run_sql("delete from nodes where name='201'", False)
    #print 'after delete:', run_sql("select * from nodes", True)
    
    #run_sql("DROP TABLE nodes", False)
    #run_sql("CREATE TABLE %s(%s VARCHAR(100) PRIMARY KEY, %s VARCHAR(100), %s VARCHAR(100), %s VARCHAR(100), %s VARCHAR(100), %s VARCHAR(255))" %(db_table, 'name', 'ip', 'usr', 'pwd', 'grp', 'desc'), False)


##################################################
#   Main Area
##################################################

import sys
if __name__ != '__main__':     
    operations = {
        'u' : lambda : update_record(sys.argv),
        'g' : lambda : get_records(sys.argv),
        'd' : lambda : delete_record(sys.argv),    
    }

    if len(sys.argv) > 1 and sys.argv[1] in operations.keys():
        operations[sys.argv[1]]()        
    else:
        print_usage()
else:
    test_sql()

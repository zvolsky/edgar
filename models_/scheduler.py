# coding: utf8

def xxxx():
    import vfp
    from datetime import datetime
    from time import sleep
    vfp.strtofile(str(datetime.now())+'\n', 'sch.log', 1)
    print '20%'
    sleep(2)
    print '!clear!100%'
    sleep(8)
    return False

from gluon.scheduler import Scheduler
myscheduler = Scheduler(db)

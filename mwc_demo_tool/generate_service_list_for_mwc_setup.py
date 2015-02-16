#!/usr/bin/python

service_id     = 'mwc_service'
broadcast_id   = 'mwc_bc'
service_bearer = 'mwc_sb'
user_service   = 'mwc_us'
file_urls = [
'http://10.0.10.179/ejjewwn/1.mpd',
'http://10.0.10.179/ejjewwn/2.mpd',
'http://10.0.10.179/ejjewwn/3.mpd',
'http://10.0.10.179/ejjewwn/4.mpd',
'http://10.0.10.179/ejjewwn/5.mpd',
'http://10.0.10.179/ejjewwn/6.mpd',
'http://10.0.10.179/ejjewwn/7.mpd',
'http://10.0.10.179/ejjewwn/8.mpd',
'http://10.0.10.179/ejjewwn/9.mpd',
'http://10.0.10.179/ejjewwn/10.mpd',
]
init_day  = 15
init_hour = 7
init_min  = 20
interval  = 5 #minutes

def generate_service(file_url, start_time, stop_time):
    print 'set services service %s type broadcast-service broadcast %s content %s %s on-demand once on-demand-file %s schedule start-time %s end-time %s' %(
           service_id, broadcast_id, service_bearer, user_service, file_url, start_time, stop_time)

def generate_all():    
    for i in range(len(file_urls)):
        start_min = init_min + i * interval
        start_hour = init_hour + start_min / 60
        start_day = init_day + start_hour / 24
        #print 'start DD, HH, MM:', start_day, start_hour, start_min
        start_time = '2015_02-%02dT%02d:%02d:00+00:00' %(start_day, start_hour % 24, start_min % 60)
        
        stop_min = init_min + (i+1) * interval
        stop_hour = init_hour + stop_min / 60
        stop_day = init_day + stop_hour / 24
        stop_time = '2015_02-%02dT%02d:%02d:00+00:00' %(stop_day, stop_hour % 24, stop_min % 60)
        
        generate_service(file_urls[i], start_time, stop_time)


if __name__ == '__main__':
    generate_all()

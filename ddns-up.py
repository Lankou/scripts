#!/usr/bin/env python
#-*- coding: utf-8 -*-
import httplib, urllib
import time, datetime
import json
import os, platform

"""
User Settings
You only need to change settings in this section.
"""
settings = dict(
    login_email = "webmaster@example.com",        # change to your email
    login_password = "swordfish",                 # change to your password
    format = "json",                                # DO NOT CHANGE!!
    record_line = "默认",                           # DO NOT CHANGE!!
)
dyndomain = "ddns.example.com"                      # change to your dynamic domain
update_interval = 6

###################################################################################
# Initialize - you don't need to change this.
# Only support one level of subdomain at this moment (xxxxx.example.com)
# TODO: figure out a way to parse domain names correctly other than using extra
# TODO: add support for updating multiple domains
# TODO: add logging
# libs like tldextract
domain = dyndomain.split('.', 1)[1]
subdomain = dyndomain.split('.', 1)[0]
settings.update(dict(sub_domain=subdomain))
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/json"}

def ts():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return timestamp

if platform.system() == 'Linux':
    if os.path.isfile('/var/run/ddns-up.pid'):
        with open ('/var/run/ddns-up.pid', 'r') as pidfile:
            oldpid = pidfile.read().strip()
            if os.path.exists('/proc/' + oldpid) and oldpid:
                raise RuntimeError('%s: Another process %s is still running. Terminating.' % (ts(), oldpid))
            else:
                with open('/var/run/ddns-up.pid', 'w') as pidfile:
                    try:
                        print '%s: PID file detected but old process is stale. Updating PID file.' % ts()
                        pidfile.write(str(os.getpid()))
                    except:
                        raise RuntimeError('%s: Unable to create PID file. Make sure you have write access to /var/run/' % ts())

    else:
        try:
            print '%s: PID file not found. Assuming this is the only instance running.' % ts()
            print 'Creating PID file with pid %s.' % os.getpid()
            with open('/var/run/ddns-up.pid', 'w') as pidfile:
                pidfile.write(str(os.getpid()))
        except:
            raise RuntimeError('%s: Unable to create PID file. Make sure you have write access to /var/run/' % ts())

def getinfo(infotype):
    conn = httplib.HTTPSConnection('dnsapi.cn')

    if infotype == 'domid':
        try:
            conn.request("POST", "/Domain.List", urllib.urlencode(settings), headers)
            doms = json.loads(conn.getresponse().read())['domains']

            for names in doms:
                domlist = []
                domlist.append(names['name'])

                if names['name'] == domain:
                    domid = names['id']
                    settings.update(dict(domain_id=domid))
                    print '%s: ID for domain %s fetched, ID %s' % (ts(), domain, domid)

            if 'domain_id' not in settings:
                raise ValueError('%s: Domain %s cannot be found under account %s!' % (ts(), domain, settings.get('login_email')))

        except KeyError, e:
            raise KeyError('%s: %s field not found in server response. Please check your login information.' % (ts(), e))

    elif infotype == 'recid':
        try:
            conn.request("POST", "/Record.List", urllib.urlencode(settings), headers)
            recs = json.loads(conn.getresponse().read())['records']

            for records in recs:
                reclist = []
                reclist.append(records['name'])

                if records['name'] == subdomain:
                    recid = records['id']
                    settings.update(dict(record_id=recid))
                    print '%s: ID for subdomain %s fetched, ID %s' % (ts(), subdomain, recid)

            if 'record_id' not in settings:
                raise ValueError('%s: Subdomain %s cannot be found under %s!' % (ts(), subdomain, domain))

        except KeyError, e:
            raise KeyError('%s: %s field not found in server response. Please check your domain.' % (ts(), e))

    elif infotype == 'recip':
        conn.request("POST", "/Record.Info", urllib.urlencode(settings), headers)
        recip = json.loads(conn.getresponse().read())['record']['value']
        if not recip:
            raise ValueError('%s: Failed to obtain record IP for %s.' % (ts(), dyndomain))
        else:
            return recip

    conn.close()

def updateddns():
    try:
        conn = httplib.HTTPSConnection('dnsapi.cn')
        conn.request("POST", "/Record.Ddns", urllib.urlencode(settings), headers)
        print conn.getresponse().read()
        if not conn.getresponse().read():
            raise IOError('%s: Failed to update DDNS record. Please check your network connectivity.' % ts())
    finally:
        conn.close()

def getip():
    conn = httplib.HTTPConnection('icanhazip.com')
    conn.request("GET", "/")
    myip = conn.getresponse().read().strip()
    conn.close()
    if not myip:
        raise IOError('%s: Unable to fetch your current IP. Please check your network connectivity.' % ts())
    else:
        return myip

if __name__ == '__main__':
    getinfo('domid')
    getinfo('recid')
    while True:
        try:
            myip = getip()
            recip = getinfo('recip')
            if recip != myip:
                print '%s: IP address changed. (Record: %s; Current: %s) -> Updating.' % (ts(), recip, myip)
                print '%s: Record: %s, updating to: %s' % (ts(), recip, myip)
                updateddns()
            else:
                print '%s: IP address not changed (%s). Sleep for %d seconds.' % (ts(), recip, update_interval)
        except Exception, e:
            print '%s: %s' % (ts(), e)
            pass
        time.sleep(update_interval)

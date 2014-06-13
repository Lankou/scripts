#!/usr/bin/env python
#-*- coding: utf-8 -*-
import httplib, urllib
import socket
import time, datetime
import json
import os, sys, platform
import logging

"""
User Settings
You only need to change settings in this section.
"""
settings = dict(
    login_email = "webmaster@example.com",        # change to your email
    login_password = "swordfish",                 # change to your password
    record_line = "默认",                           # DO NOT CHANGE!!
    format = "json",                                # DO NOT CHANGE!!
)
dyndomain = "ddns.example.com"                      # change to your dynamic domain
update_interval = 60                                # self-explanatory option
pidfile = '/tmp/ddns-up.pid'                        # pid file
logfile = '/tmp/ddns-up.log'                        # log file (set to None to disable logging)
recordtype = 'v4'                                   # record type: IPv4, IPv6 = v4, v6

###########################################################################################################
# Initialize - you don't need to change this.
# Only support one level of subdomain at this moment (xxxxx.example.com)
# TODO: figure out a way to parse domain names in the right way other than using extra libs like tldextract
# TODO: add support for updating multiple domains
domain = dyndomain.split('.', 1)[1]
subdomain = dyndomain.split('.', 1)[0]
settings.update(dict(sub_domain=subdomain))
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/json"}
logger = logging.getLogger('DNSPod DDNS Updater')
if logfile is None:
    logging.basicConfig(level=logging.INFO)
    logger.info('NOTICE: Logging is disabled. Sending output to stdout.')
else:
    logging.basicConfig(filename=logfile, level=logging.INFO)

def ts():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return timestamp

if platform.system() == 'Linux':
    if os.path.isfile(pidfile):
        with open (pidfile, 'r') as pf:
            oldpid = pf.read().strip()
            if os.path.exists('/proc/' + oldpid) and oldpid and os.path.basename(__file__) in oldpid:
                logger.error('%s: Another process %s is still running. Terminating.', ts(), oldpid)
                sys.exit(1)
            else:
                with open(pidfile, 'w') as pf:
                    try:
                        logger.info('%s: PID file detected but old process is stale. Updating PID file.', ts())
                        pf.write(str(os.getpid()))
                    except:
                        logger.error('%s: Unable to create PID file. Make sure you have write access to %s', ts(), pidfile, exc_info=True)
                        raise
    else:
        try:
            logger.info('%s: PID file not found. Assuming this is the only instance running.', ts())
            logger.info('%s: Creating PID file with pid %s.', ts(), os.getpid())
            with open(pidfile, 'w') as pf:
                pf.write(str(os.getpid()))
        except:
            logger.error('%s: Unable to create PID file. Make sure you have write access to %s', ts(), pidfile, exc_info=True)
            raise

def getinfo(infotype):
    try:
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
                        logger.info('%s: ID for domain %s fetched, ID %s', ts(), domain, domid)

                if 'domain_id' not in settings:
                    logger.error('%s: Domain %s cannot be found under account %s!', ts(), domain, settings.get('login_email'))
                    sys.exit(1)

            except KeyError, e:
                logger.error('%s: %s field not found in server response. Please check your login information.', ts(), e, exc_info=True)
                raise

            except socket.gaierror:
                logger.error('%s: Unable to connect to server. Retrying in %d seconds.', ts(), update_interval, exc_info=True)
                time.sleep(update_interval)
                getinfo('domid')

        elif infotype == 'recid':
            try:
                conn.request("POST", "/Record.List", urllib.urlencode(settings), headers)
                recs = json.loads(conn.getresponse().read())['records']

                for records in recs:
                    reclist = []
                    reclist.append(records['name'])

                    if recordtype == 'v4':
                        if records['name'] == subdomain and records['type'] == 'A':
                            recid = records['id']
                            settings.update(dict(record_id=recid))
                            logger.info('%s: ID for subdomain %s fetched, ID %s', ts(), subdomain, recid)
                    elif recordtype == 'v6':
                        if records['name'] == subdomain and records['type'] == 'AAAA':
                            recid = records['id']
                            settings.update(dict(record_id=recid))
                            logger.info('%s: ID for subdomain %s fetched, ID %s', ts(), subdomain, recid)
                    else:
                        logger.error('%s: Wrong record type %s. Please check your settings.', ts(), recordtype)
                        sys.exit(1)

                if 'record_id' not in settings:
                    logger.error('%s: Subdomain %s with record type %s cannot be found under %s!', ts(), subdomain, recordtype, domain)
                    sys.exit(1)

            except KeyError, e:
                logger.error('%s: %s field not found in server response. Please check your domain.', ts(), e, exc_info=True)
                raise

            except socket.gaierror:
                logger.error('%s: Unable to connect to server. Retrying in %d seconds.', ts(), update_interval, exc_info=True)
                time.sleep(update_interval)
                getinfo('recid')

        elif infotype == 'recip':
            try:
                conn.request("POST", "/Record.Info", urllib.urlencode(settings), headers)
                recip = json.loads(conn.getresponse().read())['record']['value']
                if not recip:
                    logger.error('%s: Failed to obtain record IP for %s.', ts(), dyndomain)
                    sys.exit(1)
                else:
                    return recip

            except socket.gaierror:
                logger.error('%s: Unable to connect to server. Retrying in %d seconds.', ts(), update_interval, exc_info=True)
                time.sleep(update_interval)
                getinfo('recip')

    finally:
        conn.close()

def updateddns():
    try:
        cur_ip = getip(recordtype)
        settings.update(dict(value=cur_ip))
        conn = httplib.HTTPSConnection('dnsapi.cn')
        conn.request("POST", "/Record.Ddns", urllib.urlencode(settings), headers)
        if not conn.getresponse().read():
            logger.error('%s: Failed to update DDNS record. Will retry in next attempt.', ts())
        else:
            logger.info('%s: DDNS record updated.', ts())

    except socket.gaierror:
        logger.error('%s: Unable to connect to server. Will retry in next attempt.', ts(), exc_info=True)
        pass

    finally:
        conn.close()

def getip(rt):
    try:
        if rt == 'v4':
            conn = httplib.HTTPConnection('icanhazip.com')
            conn.request("GET", "/")
            myip = conn.getresponse().read().strip()
        elif rt == 'v6':
            conn = httplib.HTTPConnection('ipv6.icanhazip.com')
            conn.request("GET", "/")
            myip = conn.getresponse().read().strip()
        else:
            logger.error('%s: Wrong record type %s. Please check your settings.', ts(), rt)
            sys.exit(1)


        if not myip:
            logger.error('%s: Unable to fetch your current IP. Will retry in next attempt.', ts())
        else:
            return myip

    except socket.gaierror:
        logger.error('%s: Unable to connect to server. Will retry in next attempt.', ts(), exc_info=True)
        pass

    finally:
        conn.close()

if __name__ == '__main__':
    getinfo('domid')
    getinfo('recid')
    while True:
        try:
            myip = getip(recordtype)
            recip = getinfo('recip')
            if recip != myip:
                logger.info('%s: IP address changed. (Record: %s; Current: %s) -> Updating.', ts(), recip, myip)
                logger.info('%s: Record: %s, updating to: %s', ts(), recip, myip)
                updateddns()
            else:
                logger.info('%s: IP address not changed (%s). Sleep for %d seconds.', ts(), recip, update_interval)
        except Exception, e:
            logger.error('%s: %s', ts(), e)
            pass
        time.sleep(update_interval)

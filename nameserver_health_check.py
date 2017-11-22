#!/usr/bin/env python3
#!-*- coding: utf-8 -*-
# nameserver_health_check
# author: jmdarville

import socket
import dns
import dns.resolver
import dns.query
import ipaddress
import os
from threading import Timer
import smtplib
import email
from email.mime.text import MIMEText


nameserver_list = '/path/to/list/of/nameservers'
# Would multiple domains and records be better?
domain = 'bbc.co.uk'
record = 'A'

resolver = dns.resolver.Resolver(configure = False)
resolver.timeout = 2
resolver.lifetime = 1

def send_alert(nameserver, subject, details):
  content = str(details)
  message = MIMEText(content, 'plain')
  message['From'] = ''
  message['To'] = ''
  message['Subject'] = '[' + nameserver + '] ' + subject
  full_message = message.as_string()

  server = smtplib.SMTP("localhost")
  server.sendmail("", "", full_message)
  server.close()

#need to check that the namserver actually exists before
# querying it. Assume that it doesn't
def does_nameserver_exist(server):
  exists = False
  try:
    nameserver_ip = socket.gethostbyname(server)
    exists = True
  except:
     socket.error
  return exists

def ping(host):
  #default behaviour is to assume it's down
  down = True
  response = os.system("ping -c 1 -W 2 " + host + " >/dev/null")

  if response == 0:
    down = False
  return down

# This will be used only if the nameserver exists to avoid the script failing
# because it cannot resolve the nameserver's hostname
def check_nameserver(server):

  nameserver_ip = socket.gethostbyname(server)
  status = 0
  if nameserver_ip:
    # assume the nameserver is dead and try to falsify this
    # dead = True
    try:
      query = dns.message.make_query(domain, dns.rdatatype.NS)
      response = dns.query.udp(query, nameserver_ip, timeout=2)
      #response = resolver.query(query)
      #print(response)
      rcode = response.rcode()
    
      # To view the rcode in human readable format use this
      #rcode = dns.rcode.to_text(rc)
      status = dns.rcode.to_text(rcode)
      #return dns.rcode.to_text(rcode)
    except dns.exception.DNSException as ex:
      status = ex.args[0]

    return status
  else:
    print('Undefined Error')

# Iterate over the nameservers in the ns_list
with open(nameserver_list, 'r') as ns:
  nameservers = ns.read().splitlines()
  for nameserver in nameservers:
    if does_nameserver_exist(nameserver) is True:
      status = check_nameserver(nameserver) 
      if status  == 'NXDOMAIN':
        send_alert(nameserver, 'Warning: Invalid Domain', domain + ' does not exist. Please enter a valid domain')
      elif status == 'REFUSED':
        send_alert(nameserver, 'Warning: Query Refused', ' Query was refused ')
      elif status == 'FORMERR':
        send_alert(nameserver, 'Warning: Malformatted Query', ' Server could not interpret the query. Please check')
      elif status == 'SERVFAIL':
        send_alert(nameserver, 'Warning: Server Failure', ' Server could not process the query. Please check')
      elif status == 'The DNS operation timed out.':
        send_alert(nameserver, 'Warning: Query Timed out', ' The DNS query time out. Please check')



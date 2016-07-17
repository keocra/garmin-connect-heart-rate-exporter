#!/usr/bin/python

"""
File: gchrexport.py
Original Author: Kyle Krafka (https://github.com/kjkjava/)
Fork: Moritz Borgmann (https://github.com/keocra/)
Date: Juli 17, 2016

Description:    Use this script to export your heart rate informations from garmin connect
                See README.md for more information.
"""

from urllib import urlencode
from datetime import datetime, timedelta
from getpass import getpass
from sys import argv
from os.path import isdir
from os.path import exists
from os import mkdir

import urllib2, cookielib, json

import argparse

script_version = '1.0.0'
current_date = datetime.now().strftime('%Y-%m-%d')
activities_directory = './' + current_date + '_garmin_connect_export'

parser = argparse.ArgumentParser()

parser.add_argument('--version', help="print version and exit", action="store_true")
parser.add_argument('--username', help="your Garmin Connect username (otherwise, you will be prompted)", nargs='?')
parser.add_argument('--password', help="your Garmin Connect password (otherwise, you will be prompted)", nargs='?')

parser.add_argument('-d', '--directory', nargs='?', default=activities_directory,
                    help="the directory to export to (default: './YYYY-MM-DD_garmin_connect_export')")

parser.add_argument('-s', '--startDate', nargs='?',
                    help="From which date on the data should get downloaded. (otherwise, you will be prompted)")

parser.add_argument('-e', '--endDate', nargs='?',
                    help="Until which date the data should get downloaded. (otherwise, you will be prompted)")

parser.add_argument('-o', '--overwrite', nargs='?', default="false",
                    help="If set to true it will overwrite existing files.")

parser.add_argument('-i', '--dayInterval', nargs='?', default=1,
                    help="In which day interval the data should get downloaded.")

args = parser.parse_args()

username = args.username = args.username if args.username else raw_input('Username: ')
password = args.password = args.password if args.password else getpass()
args.startDate = args.startDate if args.startDate else raw_input('Start-Date (YYYY-MM-DD): ')
args.endDate = args.endDate if args.endDate else raw_input('End-Date (YYYY-MM-DD): ')

if args.version:
    print argv[0] + ", version " + script_version
    exit(0)

print 'Welcome to Garmin Connect Heart Rate Exporter!'
# Create directory for data files.
if isdir(args.directory) and args.overwrite.lower() == "false":
    print 'Warning: Output directory already exists. Will skip already-downloaded.'
print ""

print "Your option settings:"
print "\tStart-Date:", args.startDate
print "\tEnd-Date:", args.endDate
print "\tDay interval:", args.dayInterval
print "\tOverwriting files: " + ("yes" if args.overwrite.lower() == "true" else "no")
print "\tOutput dir: " + args.directory
print "\tUsername: " + args.username
print "\tPassword: " + "**** (you won't think we will show something useful over here, did you? even the asterix are always four ;-))"
print "\n"

cookie_jar = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))


# url is a string, post is a dictionary of POST parameters, headers is a dictionary of headers.
def http_req(url, post=None, headers={}):
    request = urllib2.Request(url)
    request.add_header('User-Agent',
                       'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/1337 Safari/537.36')  # Tell Garmin we're some supported browser.
    for header_key, header_value in headers.iteritems():
        request.add_header(header_key, header_value)
    if post:
        post = urlencode(post)  # Convert dictionary to POST parameter string.
    response = opener.open(request, data=post)  # This line may throw a urllib2.HTTPError.

    # N.B. urllib2 will follow any 302 redirects. Also, the "open" call above may throw a urllib2.HTTPError which is checked for below.
    if response.getcode() != 200:
        raise Exception('Bad return code (' + response.getcode() + ') for: ' + url)

    return response.read()


# URLs for various services.
url_gc_login = 'https://sso.garmin.com/sso/login?service=https%3A%2F%2Fconnect.garmin.com%2Fpost-auth%2Flogin&webhost=olaxpw-connect04&source=https%3A%2F%2Fconnect.garmin.com%2Fen-US%2Fsignin&redirectAfterAccountLoginUrl=https%3A%2F%2Fconnect.garmin.com%2Fpost-auth%2Flogin&redirectAfterAccountCreationUrl=https%3A%2F%2Fconnect.garmin.com%2Fpost-auth%2Flogin&gauthHost=https%3A%2F%2Fsso.garmin.com%2Fsso&locale=en_US&id=gauth-widget&cssUrl=https%3A%2F%2Fstatic.garmincdn.com%2Fcom.garmin.connect%2Fui%2Fcss%2Fgauth-custom-v1.1-min.css&clientId=GarminConnect&rememberMeShown=true&rememberMeChecked=false&createAccountShown=true&openCreateAccount=false&usernameShown=false&displayNameShown=false&consumeServiceTicket=false&initialFocus=true&embedWidget=false&generateExtraServiceTicket=false'
url_gc_post_auth = 'https://connect.garmin.com/post-auth/login?'
url_gc_search = 'http://connect.garmin.com/proxy/activity-search-service-1.0/json/activities?'
url_gc_heart_rate = 'https://connect.garmin.com/modern/proxy/wellness-service/wellness/dailyHeartRate/'
url_gc_original_activity = 'https://connect.garmin.com/modern/proxy/download-service/files/wellness/'

# Initially, we need to get a valid session cookie, so we pull the login page.
http_req(url_gc_login)

# Now we'll actually login.
post_data = {'username': username, 'password': password, 'embed': 'true', 'lt': 'e1s1', '_eventId': 'submit',
             'displayNameRequired': 'false'}  # Fields that are passed in a typical Garmin login.
http_req(url_gc_login, post_data)

# Get the key.
login_ticket = None
for cookie in cookie_jar:
    if cookie.name == 'CASTGC':
        login_ticket = cookie.value
        break

if not login_ticket:
    raise Exception('Did not get a ticket cookie. Cannot log in. Did you enter the correct username and password?')

# Chop of 'TGT-' off the beginning, prepend 'ST-0'.
login_ticket = 'ST-0' + login_ticket[4:]

http_req(url_gc_post_auth + 'ticket=' + login_ticket)

# We should be logged in now.
if not isdir(args.directory):
    mkdir(args.directory)

search_params = {'start': 0, 'limit': 1}
# Query Garmin Connect
result = http_req(url_gc_search + urlencode(search_params))
json_results = json.loads(result)

activities = json_results['results']['activities']
url_user_name = activities[0]["activity"]["username"]

# build json download url
url_gc_heart_rate += str(url_user_name) + '?date='

sdate = datetime.strptime(args.startDate, "%Y-%m-%d")
edate = datetime.strptime(args.endDate, "%Y-%m-%d")
tdelta = timedelta(days=abs(args.dayInterval))

if sdate > edate:
    tmp = edate
    edate = sdate
    sdate = tmp

cdate = sdate
while cdate <= edate:
    firstRound = False
    json_data_filename = args.directory + "/" + cdate.strftime("%Y-%m-%d") + ".json"
    zip_data_filename = args.directory + "/" + cdate.strftime("%Y-%m-%d") + ".zip"

    if (args.overwrite.lower() == "true" and not isdir(json_data_filename) and not isdir(zip_data_filename)) or \
        (args.overwrite.lower() == "false" and ((not exists(json_data_filename) and not isdir(zip_data_filename)) or (not exists(zip_data_filename) and not isdir(json_data_filename)))):
        try:
            print "Process date:", cdate.strftime("%Y-%m-%d")

            url = url_gc_heart_rate + cdate.strftime("%Y-%m-%d")
            data = http_req(url)

            dailyHeartRate = json.loads(data)

            if dailyHeartRate["heartRateValues"]:
                with open(json_data_filename, "wb") as fh:
                    json.dump(dailyHeartRate, fh, indent=1)

                zip_url = url_gc_original_activity + cdate.strftime("%Y-%m-%d")
                zip_data = http_req(zip_url)

                with open(zip_data_filename, "wb") as fh:
                    fh.write(zip_data)
                    fh.flush()
            else:
                print "There is no heart rate data at this date (" + cdate.strftime("%Y-%m-%d") + ")."
        except:
            print "Something went wrong on date:", cdate .strftime("%Y-%m-%d")
    else:
        if args.overwrite.lower() == "true":
            print "There is already a folder with the name \"" + json_data_filename + "\" or \"" + zip_data_filename + "\""
        else:
            print "Both files (" + json_data_filename + ", " + zip_data_filename + ") already exist. Skip this date: " + cdate.strftime("%Y-%m-%d")

    if cdate == edate:
        break
    elif cdate + tdelta >= edate:
        cdate = edate
    else:
        cdate += tdelta

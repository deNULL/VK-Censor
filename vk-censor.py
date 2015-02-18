import json, getpass, sys, os.path, urllib, urllib2, time

# Authenticate as iOS app

if os.path.isfile('vk-censor-auth.json'):
  auth = json.load(open('vk-censor-auth.json', 'r'))
else:
  username = raw_input('Enter your VK login (phone or email): ')
  password = getpass.getpass('Enter your VK password: ')

  request = {
    'client_id': 3140623,
    'client_secret': 'VeWdmVclDCtn6ihuP1nt',
    'grant_type': 'password',
    'username': username,
    'password': password,
    '2fa_supported': 1,
  }

  try:
    auth = json.loads(urllib2.urlopen('https://api.vk.com/oauth/token', urllib.urlencode(request)).read())
  except urllib2.HTTPError, error:
    auth = json.loads(error.read())

  if auth['error'] == 'need_validation':
    request['code'] = raw_input('Enter the code you received in SMS: ')
    try:
      auth = json.loads(urllib2.urlopen('https://api.vk.com/oauth/token', urllib.urlencode(request)).read())
    except urllib2.HTTPError, error:
      auth = json.loads(error.read())

  if 'error' in auth:
    print 'Unknown error: ' + auth['error'] + ', quitting'
    sys.exit()

  json.dump(auth, open('vk-censor-auth.json', 'w'))

if not 'access_token' in auth:
  print 'access_token is missing, quitting'
  sys.exit()

# Now auth['access_token'] should contain valid unlimited oauth token

request = {
  'filters': 'post,ads',
  'count': 100,
  'v': '5.28',
  'access_token': auth['access_token']
}

print 'Checking for news every 10s... (Ctrl-C to abort)'
while True:
  try:
    feed = json.loads(urllib2.urlopen('https://api.vk.com/method/newsfeed.get', urllib.urlencode(request)).read())
  except urllib2.HTTPError, error:
    print 'Oops, error: {}'.format(error.read())

  if 'response' in feed:
    if 'items' in feed['response']:
      items = feed['response']['items']
      #print '{} results'.format(len(items))

      found = False
      for item in items:
        if not found and 'date' in item:
          found = True
          #request['start_time'] = item['date'] # Limit next request

        if 'type' in item and item['type'] == 'ads':
          print 'Found {} ad:'.format(len(item['ads']))
          for ad in item['ads']:
            print '  {0} ({1})'.format(ad['title'].encode('utf-8'), ad['description'].encode('utf-8'))

            reqhide = {
              'ad_data': ad['ad_data'],
              'v': '5.28',
              'access_token': auth['access_token']            
            }

            try:
              resp = urllib2.urlopen('https://api.vk.com/method/adsint.hideAd', urllib.urlencode(reqhide)).read()
              if 'response' in resp and 'success' in resp['response'] and resp['response']['success'] == 1:
                print '  => successfully hidden'
              else:
                print 'Oops, error: {}'.format(resp)
            except urllib2.HTTPError, error:
              print 'Oops, error: {}'.format(error.read())
              
            time.sleep(1)

          #print json.dumps(item, indent=2, ensure_ascii=False)

    #if 'next_from' in feed['response']:
    #  request['start_from'] = feed['response']['next_from']
  else:
    print 'Oops, error: {}'.format(json.dumps(feed, ensure_ascii=False))
  time.sleep(10)
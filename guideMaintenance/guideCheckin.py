import sys
import json
import os
import requests

def getSubscription():
    user = os.environ.get('PENDO_USER')
    subscription = os.environ.get('PENDO_SUBSCRIPTION')
    assert user
    assert subscription
    url = "https://app.pendo.io/api/s/%s/user/%s/setting/impersonate.subscription" % (subscription, user)
    headers = {'cookie': 'pendo.sess=%s' % getSessionId() }
    impersonate = requests.get(url, headers = headers )
    return json.loads(impersonate.content)['value']

def getStepUrl(guideId, stepId):
    subscription = getSubscription()
    rootUrl = 'https://app.pendo.io/api/s/%s/guide/' % subscription
    url = "%s%s/step/%s" % (rootUrl, guideId, stepId)
    return url

def getSessionId():
    sessionId = os.environ.get('PENDO_SESS')
    assert sessionId
    return sessionId

def getStepContent(guideId, stepId):
    url = getStepUrl(guideId, stepId)
    headers = {'cookie': 'pendo.sess=%s' % getSessionId() }
    step = requests.get(url, headers = headers )
    # TODO check response code and raise error
    return step.content

def putStepContent(guideId, stepId, json):
    url = getStepUrl(guideId, stepId)
    headers = {'cookie': 'pendo.sess=%s' % getSessionId(),
               'Content-Type':'application/json'
              }
    step = requests.put(url, headers = headers, data = json )
    # TODO check response code and raise error
    return step.status_code

#http://code.activestate.com/recipes/576644-diff-two-dictionaries/
def dict_diff(d1, d2, NO_KEY='<KEYNOTFOUND>'):
    a = d1.keys()
    b = d2.keys()
    both = []
    for e in a:
        if e in b:
            both.append(e)
    diff = {k:(d1[k], d2[k]) for k in both if d1[k] != d2[k]}
    diff.update({k:(d1[k], NO_KEY) for k in list(set(d1.keys()) - set(both))})
    diff.update({k:(NO_KEY, d2[k]) for k in list(set(d2.keys()) - set(both))})
    return diff

destructive = False
if len(sys.argv) > 1 and sys.argv[1] == 'y':
    destructive = True

rootDir = '.'
for dirName, subdirList, fileList in os.walk(rootDir):
    for fname in fileList:
        if fname.endswith(".html"):
            step_id = fname[:-5][7:]   # drop "s-1234-" and ".html"
            #print(getStepUrl(dirName[2:], step_id))
            content = getStepContent(dirName[2:], step_id)
            upstreamStep = json.loads(content)
            localStepMeta = json.load(open("%s/%s.meta" %(dirName, fname[:-5]), 'rb'))  # use stepnum from the original filename
            localStepContent = open("%s/%s" %(dirName, fname), 'rb')
            localStepMeta[u'content'] = localStepContent.read().decode('utf8')
            stepDiff = dict_diff(localStepMeta,upstreamStep)
            #ignore all non-content differences for now
            if stepDiff.has_key('content'):
                # extra rules locally, might just want to replace the content of upstream
                print "updating content for guide %s -> %s" % (localStepMeta['guideId'], fname)
                upstreamStep['content'] = localStepMeta['content']
                if destructive:
                    print putStepContent(dirName[2:], step_id, json.dumps(upstreamStep))
                else:
                    print "- non-destructive mode: no changes actually uploaded."

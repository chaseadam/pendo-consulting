import json
import os
import requests

def getStepUrl(guideId, stepId):
    subscription = ''
    rootUrl = 'https://app.pendo.io/api/s/%s/guide/' % subscription
    url = "%s%s/step/%s" % (rootUrl, guideId, stepId)
    return url

def getSessionId():
    sessionId = ''
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

rootDir = '.'
for dirName, subdirList, fileList in os.walk(rootDir):
    for fname in fileList:
        if fname.endswith(".content"):
            print(getStepUrl(dirName[2:], fname[:-8]))
            content = getStepContent(dirName[2:], fname[:-8])
            upstreamStep = json.loads(content)
            localStepMeta = json.load(open("%s/%s.meta" %(dirName, fname[:-8]), 'rb'))
            localStepContent = open("%s/%s" %(dirName, fname), 'rb')
            localStepMeta[u'content'] = localStepContent.read().decode('utf8')
            stepDiff = dict_diff(localStepMeta,upstreamStep)
            #ignore all non-content differences for now
            if stepDiff.has_key('content'):
                # extra rules locally, might just want to replace the content of upstream
                print "updating content for guide %s" % localStepMeta['guideId']
                upstreamStep['content'] = localStepMeta['content']
                print putStepContent(dirName[2:], fname[:-8], json.dumps(upstreamStep))
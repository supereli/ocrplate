import sys
sys.path.append("packages")
import os
#import requests
import json
#import pytesseract
#from PIL import Image
import urllib2
#import ssl
import re
from StringIO import StringIO


#if hasattr(ssl, '_create_unverified_context'):
#   ssl._create_default_https_context = ssl._create_unverified_context

def createPayloadDict():
   payload = os.getenv('PAYLOAD_FILE')
#   print(payload)
   payloadfile = open(payload)
   payloadstring = payloadfile.read()
#   print(payloadstring)
   jsondict = json.loads(payloadstring)
   return jsondict

def printAndOcrImage(imageName,imageUrl):
    print('OCR on plate: ')
    theoutput=os.popen("alpr ./images/" + imageName).read()
#    print(theoutput)
    return(theoutput)
#    print(result_string)
#    return(result_string)

def isolateHighestConfidence(ocroutput):
   print(re.findall(r"results\s.*- (.*)\t confidence",ocroutput)[0])

def downloadImage(imageName,imageUrl):
   imageget = urllib2.urlopen(imageUrl)
   with open('./images/' + imageName,'wb') as output:
      output.write(imageget.read())

#print(os.getenv('PAYLOAD_FILE'))
os.system("sudo ln /dev/null /dev/raw1394")
payloaddict=createPayloadDict()
theImageUrl=payloaddict['imageUrl']
theImageName=re.findall("inbox\/(.*)\.",payloaddict['imageUrl'])[0] + '.jpg'
#theImageName='3.jpg'
#print(theImageName)
#print(theImageUrl)

downloadImage(theImageName,theImageUrl)
isolateHighestConfidence(printAndOcrImage(theImageName,theImageUrl))
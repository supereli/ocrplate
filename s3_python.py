import sys
sys.path.append("packages")
import boto3
import os
import json
import re
import requests
from datetime import datetime, timezone
import time


payload = os.environ.get('PAYLOAD_FILE')
print("ConfigFile: %s" % payload)

if not(payload is None):
	with open(payload) as data_file:
		options = json.load(data_file)
else:
	print("No Payload found")
	exit(2)

if "aws_access_key" in options:
	aws_access_key = options["aws_access_key"]
else:
	print("aws_access_key not specified in payload should be \"aws_access_key\"")
	exit(3)

if "endpoint_url" in options:
	endpoint_url = options["endpoint_url"]
else:
	print("endpoint_url not specified in payload should be \"endpoint_url\":\"https://IRONMQSERVER\"")
	exit(4)

if "aws_secret_key" in options:
	aws_secret_key = options["aws_secret_key"]
else:
	print("No aws_secret_key specified")
	exit(1)

if "region" in options:
	region = options["region"]
else:
	print("No region specified, defaulting to us-east-1, not sure this is needed")

if "cluster" in options:
	cluster = options["cluster"]
else:
	print("No cluster specifying, defaulting to default")

if "publish_key" in options:
	publish_key = options["publish_key"]
else:
	print("No Publish_key specified")
	exit(1)

if "subscribe_key" in options:
	subscribe_key = options["subscribe_key"]
else:
	print("No subscribe_key specified")
	exit(1)

if "dockerimage" in options:
	dockerimage = options["dockerimage"]
else:
	print("No child dockerimage specified")
	exit(1)

if "token" in options:
	token = options["token"]
else:
	print("No token specified")
	exit(1)

if "projectid" in options:
	projectid = options["projectid"]
else:
	print("projectid not specified")
	exit(1)

if "detect_image" in options:
	detect_image = options["detect_image"]
else:
	print("detect_image not specified")
	exit(1)

if "aws_s3_bucket" in options:
	aws_s3_bucket = options["aws_s3_bucket"]

full_url = "http://" + endpoint_url

logDir = "./logs"
if not(os.path.isdir(logDir)):
	os.makedirs(logDir)

logFile = "%s/s3_python.log" % logDir

try:
	os.remove(logFile)
except OSError:
	pass

def logOut(msg):
	log = open(logFile, 'a')
	data = "%s: %s" % (datetime.now(), msg)
	log.write(data)
	log.write("\n")
	log.close

def triggerWorker(fileName, fileKey):
	msgType = "Notification"
	subject = "Openstack Image Notification"
	message = "{\\\\\\\"Records\\\\\\\":[{\\\\\\\"s3\\\\\\\":{\\\\\\\"bucket\\\\\\\":{\\\\\\\"name\\\\\\\":\\\\\\\"%s\\\\\\\"},\\\\\\\"object\\\\\\\":{\\\\\\\"key\\\\\\\":\\\\\\\"%s\\\\\\\"}}}]}" % (aws_s3_bucket,fileKey)
	payloadStart = "{\"tasks\": [{\"label\":\"%s\",\"code_name\":\"%s\", \"cluster\":\"%s\", \"payload\":\"{" % (fileName, detect_image, cluster)
#	payloadData =  " \\\"Type\\\":\\\"%s\\\",\\\"Subject\\\":\\\"%s\\\",\\\"endpoint_url\\\":\\\"%s\\\"" % (msgType, subject,endpoint_url)
#	payloadData1 = ",\\\"cluster\\\":\\\"%s\\\",\\\"aws_access_key\\\":\\\"%s\\\",\\\"aws_secret_key\\\":\\\"%s\\\"" % (cluster,aws_access_key,aws_secret_key)
#	payloadData2 = ",\\\"publish_key\\\":\\\"%s\\\",\\\"subscribe_key\\\":\\\"%s\\\",\\\"dockerimage\\\":\\\"%s\\\"" % (publish_key,subscribe_key,dockerimage)
#	payloadData3 = ",\\\"token\\\":\\\"%s\\\",\\\"projectid\\\":\\\"%s\\\"" % (token, projectid)
#	payloadData4 = ",\\\"Message\\\":\\\"%s\\\"" % message
#	payloadEnd = "}\"}]}" 
#	payload = payloadStart + payloadData + payloadData1 + payloadData2 + payloadData3 + payloadData4 + payloadEnd

#	payload = payloadStart + "\"imageUrl\": \"" + endpoint_url + "\"}\"}"
	theImageURL = "\\\"imageUrl\\\": \\\"http://" + endpoint_url + "/" + aws_s3_bucket + "/" + fileKey + "\\\"}\"}]}"
	payload = payloadStart + theImageURL

	print(payload)
	logOut(payload)

	url = "https://worker-aws-us-east-1.iron.io/2/projects/" + projectid + "/tasks"
	oAuthString = "OAuth %s" % token
	
	headers = {
		'authorization': oAuthString,
		'content-type': "application/json",
		'cache-control': "no-cache"
	}

	response = requests.request("POST", url, data=payload, headers=headers)

	print(response.text)
	logOut(response.text)

stopLoop = False
stopFile = "stop_check"

sentFiles = {}

clearTime = datetime.now()
while stopLoop == False:
	if os.path.isfile(stopFile):
		stopLoop = True
	cTime = datetime.now()
	eTime = cTime - clearTime
	
	#time.sleep(1)
	s3 = boto3.resource(
		's3',
	    aws_access_key_id=aws_access_key,
	    aws_secret_access_key=aws_secret_key,
	    endpoint_url=full_url
	    )

	bucket = s3.Bucket(aws_s3_bucket)
	dt = datetime.now(timezone.utc)
	# print s3
	for object in bucket.objects.all():
		
	    #Currently harcoding to the inbox folder
		objectDt = object.last_modified
		#objectTime = datetime.strptime(objectDt, "%y-%m-%d %H:%M:%S")
		diff = dt - objectDt
		# if (re.match('inbox/([A-Za-z0-9-_])', object.key) is not None):
		# 	print("%s (%s)" % (object.key, diff.total_seconds()))
		# 	logOut("%s (%s)" % (object.key, diff.total_seconds()))
		saveKey = object.key
		#name = re.split('inbox/', object.key)[1]
		alreadySent = 0
		if eTime.total_seconds() > 60:
		#print("Clearing history")
			#sentFiles = {}
			#cTime = datetime.now()
			clearTime = cTime

		for broken in sentFiles:
			#print(broken, saveKey)
			if broken == saveKey and objectDt == sentFiles[broken]:
				alreadySent = 1

		if ((abs(diff.total_seconds())  <= 10) and alreadySent == 0) and (re.match('inbox/([A-Za-z0-9-_])', saveKey) is not None):
			# sentFiles[saveKey] = diff.total_seconds()
			print(saveKey)
			print(sentFiles)
			sentFiles[saveKey] = objectDt
			# exit(1)
			# not(saveKey in sentFiles) and 
			print("File: %s Time: %s" % (saveKey,objectDt))
			logOut("File: %s Time: %s" % (saveKey,objectDt))
			
			print(sentFiles)
			logOut(sentFiles)
			fileName = re.split('inbox/', object.key)[1]
			triggerWorker(fileName,saveKey)

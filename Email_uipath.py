import json
import boto3
import email
import base64
import requests
from sapcai import Request, Connect

#creating s3 client object
global s3
s3 = boto3.client('s3')

def lambda_handler(event, context):
    
    print(event, end="\n")
    
    #Getting bucket name
    bucket = event['Records'][0]['s3']['bucket']['name']
    print(bucket,end="\n")
    
    #Getting File name 
    FileName = event['Records'][0]['s3']['object']['key']
    print(FileName, end="\n")
    
    #Getting subject and mesage from mail body
    subject, message = get_email_content(bucket, FileName)
    print("sub : " + subject)
    print("msg : " + message)
    
    #Detecting intent from message
    intent, nlp= get_intent(message)
    print("intent : " + intent)
    
    #Call corressponding job
    if(intent == "schedulemeeting"):
        return schedule_meeting(intent, subject, nlp)
    elif(intent == "cancelmeeting"):
        return cancel_meeting(intent, subject, nlp)
    elif(intent == "reschedule_meeting"):
        return reschedule_meeting(intent, subject, nlp)
    elif(intent == "add_people"):
        return add_people(intent, subject, nlp)
    elif(intent == "remove_people"):
        return remove_people(intent, subject, nlp)
    return "Invalid intent"

    
def schedule_meeting(intent, title, data):
    
    #Getting the meeting description
    description = "Meeting Remainder" if 'meet_context' not in data['results']['entities'] else data['results']['entities']['meet_context'][0]['value']
    print ("desc : " + description)
    
    #Getting the Meeting time
    if "interval" not in data['results']['entities']:
        start_time = end_time = None
        print("start : " + start_time)
    else:
        start_time = data['results']['entities']['interval'][0]['begin'].split("+")[0]
        end_time = data['results']['entities']['interval'][0]['end'].split("+")[0]
    
    print("start : " + start_time)
    print("end : " + end_time)
    
    location = data['results']['entities']['location'][0]['formatted']
    
    #Getting the meetingattenders email address as a list
    attenders_list = []
    for i in data['results']['entities']['email']:
        attenders_list.append(str(i['raw']))
    
    print("attend : ", attenders_list)
    
    #Call the trigger bot function
    return trigger_schedule_bot(intent, title, description, start_time, end_time, location, attenders_list)


def trigger_schedule_bot(intent, title, des, start, end, location, attend):
    
    #Getting the accesss token for authentication
    token = get_token()
    print(token)
    
    #getting the corressponding process key
    release_key = get_release(intent, token)
    print(release_key)
    
    #Call the schedule job function
    return schedule_job(title, des, start, end, attend, token, location, release_key)


def schedule_job(job_title, job_desc, job_start, job_end, people_list, AccToken, location, process_key):
    
    #Rest API url for starting job
    job_url = "https://platform.uipath.com/daas/nishiwejm277213/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs"
    
    #Defining Input arguments for the job
    inp_arg = {
        "Title": str(job_desc),
        "People": people_list,
        "Start_Date_Time": str(job_start),
        "End_Date_Time": str(job_end),
        "Location": "Smvec",
        "Notes": "This meeting is about : " + str(job_desc),
        "Location" : location
    }
    
    #defining the Job body
    job_body = {
        "startInfo": {
            "ReleaseKey": process_key,
            "Strategy": "Specific",
            "RobotIds": [
                43663
            ],
            "InputArguments": json.dumps(inp_arg)
        }
    }
    print("body : ",job_body)
    
    #Posting the data to UiPath orchestrator server through requests
    job_res = requests.post(job_url, data=json.dumps(job_body), headers = {
        'Content-Type' : 'application/json',
        'Authorization' : 'Bearer ' + str(AccToken),
        'X-UIPATH-TenantName' : 'nishiwejm277213'
    })
    print(job_res.json())
    
    return "Meeting Scheduled successfully..."

def cancel_meeting(intent, title, data):
    
    meeting_title = "project review"
    meet_date = data['results']['entities']['datetime'][0]['iso'].split('T')[0]
    
    print(meeting_title)
    print(meet_date)
    
    return trigger_cancel_bot(intent, meeting_title, meet_date)

def trigger_cancel_bot(intent, title, date):
    
    token = get_token()
    print(token)
    
    release_key = get_release(intent, token)
    print(release_key)
    
    return cancel_job(title, date, token, release_key)
    
def cancel_job(job_title, job_date, job_token, job_key):
    
    job_url = "https://platform.uipath.com/daas/nishiwejm277213/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs"
    
    inp_arg = {
        "Event_Name": job_title,
        "Start_Date" : job_date
    }
    
    job_body = {
        "startInfo": {
            "ReleaseKey": job_key,
            "Strategy": "Specific",
            "RobotIds": [
                43663
            ],
            "InputArguments": json.dumps(inp_arg)
        }
    }
    
    print("body : ",job_body)
    
    job_res = requests.post(job_url, data=json.dumps(job_body), headers = {
        'Content-Type' : 'application/json',
        'Authorization' : 'Bearer ' + str(job_token),
        'X-UIPATH-TenantName' : 'nishiwejm277213'
    })
    
    print(job_res.json())
    
    return "The Meeting cancelled successfully..."

    
def reschedule_meeting(intent, title, data):
    
    # old_date = data['results']['entities']['datetime'][0]['iso'].split('T')[0]
    # print("old : ", old_date)
    
    reschedule_start_date = None if 'interval' not in data['results']['entities'] else data['results']['entities']['interval'][0]['begin'].split("+")[0]
    reschedule_end_date = None if 'interval' not in data['results']['entities'] else data['results']['entities']['interval'][0]['end'].split("+")[0]
    print("st : ", reschedule_start_date)
    print("end : ", reschedule_end_date)
    
    location = None if 'location' not in data['results']['entities'] else data['results']['entities']['location'][0]['formatted']
    print("loc : ", location)
    
    title = "Meeting Remainder" if 'meet_context' not in data['results']['entities'] else data['results']['entities']['meet_context'][0]['value']
    return trigger_reschedule_bot(intent, title, reschedule_start_date, reschedule_end_date, location)
    
def trigger_reschedule_bot(intent, title, reschedule_start_date, reschedule_end_date, location):
    
    token = get_token()
    print(token)
    
    #getting the corressponding process key
    release_key = get_release(intent, token)
    print(release_key)
    
    return reshedule_job(title, reschedule_start_date, reschedule_end_date, location, token, release_key)

def reshedule_job(event_name, start, end, loc, job_token, job_key):
    
    job_url = "https://platform.uipath.com/daas/nishiwejm277213/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs"
    
    inp_arg = {
        "Events_Name" : event_name,
        "Start_Date_Time" : str(start),
        "End_Date_Time" : str(end),
        "Location" : str(loc)
    }
    
    job_body = {
        "startInfo": {
            "ReleaseKey": job_key,
            "Strategy": "Specific",
            "RobotIds": [
                43663
            ],
            "InputArguments": json.dumps(inp_arg)
        }
    }
    
    print("body : ",job_body)
    
    job_res = requests.post(job_url, data=json.dumps(job_body), headers = {
        'Content-Type' : 'application/json',
        'Authorization' : 'Bearer ' + str(job_token),
        'X-UIPATH-TenantName' : 'nishiwejm277213'
    })
    print(job_res.json())
    
    return "Meeting successfully rescheduled..."
    
def add_people(intent, title, data):
    
    attenders_list = []
    for i in data['results']['entities']['email']:
        attenders_list.append(str(i['raw']))
    
    print("attend : ", attenders_list)
    
    event_name = data['results']['entities']['meet_context'][0]['value']
    print("e : ", event_name)
    
    return trigger_add_members_bot(intent, event_name, attenders_list)
    
def trigger_add_members_bot(intent, event_name, attenders_list):
    
    token = get_token()
    print("Token : ", token)
    
    release_key = get_release(intent, token)
    print("Key : ", release_key)
    
    return add_members_job(event_name, attenders_list, token, release_key)
    
def add_members_job(event_name, attenders_list, job_token, job_key):
    
    
    job_url = "https://platform.uipath.com/daas/nishiwejm277213/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs"
    
    inp_arg = {
        "Events_Name" : str(event_name),
        "Add_Attendies" : attenders_list
    }
    
    job_body = {
        "startInfo": {
            "ReleaseKey": job_key,
            "Strategy": "Specific",
            "RobotIds": [
                43663
            ],
            "InputArguments": json.dumps(inp_arg)
        }
    }
    
    print("body : ",job_body)
    
    job_res = requests.post(job_url, data=json.dumps(job_body), headers = {
        'Content-Type' : 'application/json',
        'Authorization' : 'Bearer ' + str(job_token),
        'X-UIPATH-TenantName' : 'nishiwejm277213'
    })
    print(job_res.json())
    
    return "Members added Successfully"
    
def remove_people(intent, title, data):
    
    attenders_list = []
    for i in data['results']['entities']['email']:
        attenders_list.append(str(i['raw']))
    
    print("attend : ", attenders_list)
    
    event_name = data['results']['entities']['meet_context'][0]['value']
    print("e : ", event_name)
    
    return trigger_remove_members_bot(intent, event_name, attenders_list)
    
def trigger_remove_members_bot(intent, event_name, attenders_list):
    
    token = get_token()
    print("Token : ", token)
    
    release_key = get_release(intent, token)
    print("Key : ", release_key)
    
    return remove_members_job(event_name, attenders_list, token, release_key)
    
def remove_members_job(event_name, attenders_list, job_token, job_key):
    
    
    job_url = "https://platform.uipath.com/daas/nishiwejm277213/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs"
    
    inp_arg = {
        "Remove_People" : attenders_list,
        "Event_Name" : str(event_name)
    }
    
    job_body = {
        "startInfo": {
            "ReleaseKey": job_key,
            "Strategy": "Specific",
            "RobotIds": [
                43663
            ],
            "InputArguments": json.dumps(inp_arg)
        }
    }
    
    print("body : ",job_body)
    
    job_res = requests.post(job_url, data=json.dumps(job_body), headers = {
        'Content-Type' : 'application/json',
        'Authorization' : 'Bearer ' + str(job_token),
        'X-UIPATH-TenantName' : 'nishiwejm277213'
    })
    print(job_res.json())
    
    return "Members removed Successfully"
    
def get_release(intent, acc_token):
    
    release_url = "https://platform.uipath.com/daas/nishiwejm277213/odata/Releases"
    
    release_res = requests.get(release_url, headers = {
        'Authorization' : "Bearer " + str(acc_token),
        'Content-Type' : 'application/json',
        'X-UIPATH-TenantName' : 'nishiwejm277213'
    }).json()
    
    for i in release_res['value']:
        if i['ProcessKey'] == 'Schedule_Meeting' and intent == 'schedulemeeting':
            return release_res['value'][0]['Key']
        elif i['ProcessKey'] == 'Reshedule_Meeting' and intent == 'reschedule_meeting':
            return release_res['value'][1]['Key']
        elif i['ProcessKey'] == 'Cancel_Meeting' and intent == 'cancelmeeting':
            return release_res['value'][2]['Key']
        elif i['ProcessKey'] == 'Add_People' and intent == 'add_people':
            return release_res['value'][3]['Key']
        elif i['ProcessKey'] == 'Remove_People' and intent == 'remove_people':
            return release_res['value'][5]['Key']
            
    return None

def get_token():
    
    #Token url
    token_url = "https://account.uipath.com/oauth/token"
    
    #Defining url body
    token_body = {
        "grant_type": "refresh_token",
        "client_id": "8DEv1AMNXczW3y4U15LL3jYf62jK93n5",
        "refresh_token": "vSISMQ9CbGYdKDVajOBCjtmCfZdhXa82h_WmMSnTqzEPS"
    }
    
    
    token_res = requests.post(token_url, data=json.dumps(token_body), headers = {
        'Content-Type':'application/json',
        'X-UIPATH-TenantName':'nishiwejm277213'
    }).json()
    
    return token_res['access_token']
    
    
def get_intent(msg):
    
    #Creating request object of sapcai
    request = Request('282f398b18e8828ba1eb054b035d6fd3')
    
    #Detect intent through CAI nlp
    detect_intent = request.analyse_text(msg)
    
    #Storing the nlp response in json
    nlp_data = json.loads(detect_intent.raw)
    
    #Getting intent from the response
    intent = str(detect_intent.intent).split()
    
    return (intent[0], nlp_data)

def get_email_content(bucket_name, file_name):
    
    #Getting object from the bucket
    obj = s3.get_object(Bucket=bucket_name, Key=file_name)
    #print(obj, end="\n")
    
    #Reading full mail 
    mail = email.message_from_bytes(obj['Body'].read())
    
    #Reading subject of mail
    sub = mail['Subject']
    
    #Reading mail body
    mail_body = mail.get_payload()[0].get_payload().split("--")
    body_content = mail_body[0].replace("\r\n", " ")
    
    return (sub, body_content)
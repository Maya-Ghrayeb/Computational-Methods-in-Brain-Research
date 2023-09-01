from datetime import datetime, timedelta, timezone

from flask import Flask, redirect, request, render_template, make_response
import urllib.parse
from requests_oauthlib import OAuth1Session
import binascii
import os

# These would be provided by Garmin when you register your application
from schonbergAPI import SchonbergLabAPI

CLIENT_ID = '221a1c5e-0925-4263-b8fa-6251f7eef7c6'
CLIENT_SECRET = '8F0g1d0kBCfH6gdp2TU2GAM4uH5QAuEOzUx'
REDIRECT_URI = 'http://localhost:5000/authbborization_code'

# URL endpoints provided in Garmin's API documentation
AUTHORIZATION_URL = 'https://connect.garmin.com/oauthConfirm'
TOKEN_URL = 'https://connect.garmin.com/oauth2/token'

AUTHORIZATION_TOKEN = 'oauth_token'
AUTHORIZATION_TOKEN_SECRET = 'oauth_token'


app = Flask(__name__)

worker_key = "3377bab2c0e5b030d36fdc37f6d0d6dd1e73a92b7fb505fbfef6138daccf09be0b57699443554587a92a7a1261991a801e173af8bd1d16c15b58351aa7feeae5"
api = SchonbergLabAPI(worker_key)
#session_id = api.add_new_session(data={})['_id']
session_id=None

@app.route('/submit_id', methods=['POST'])
def submit_id():
    global session_id
    participant_id = request.form.get('participantID')

    consumer_key = CLIENT_ID
    consumer_secret = CLIENT_SECRET

    # Step 1: Acquire Unauthorized Request Token and Token Secret (from garmin server)
    request_token_url = "https://connectapi.garmin.com/oauth-service/oauth/request_token"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    r = oauth.fetch_request_token(request_token_url)
    request_token = r.get('oauth_token')
    request_token_secret = r.get('oauth_token_secret')

    # storing our request tokens for later
    os.environ['REQUEST_TOKEN'] = request_token
    os.environ['REQUEST_TOKEN_SECRET'] = request_token_secret

    authorization_url = oauth.authorization_url(AUTHORIZATION_URL)

    # Create a new session for the participant and include relevant data
    session_data = {'participant_id': participant_id,
                    'req_token': request_token,
                    'req_token_secret': request_token_secret,
                    'oauth_url': authorization_url}
    # Add the new session to the API
    new_session = api.add_new_session(data=session_data)

    session_id = new_session['_id']  # Get the session ID from the created session
    print("here")
    print(session_id)
    response = make_response("Participant ID saved successfully!")
    response.set_cookie('session_id', session_id, max_age=600)

    return response


@app.route('/first_page')
def first_page():
    return render_template('welcome.html')


@app.route('/to_garmin')
def home():
    session_id = request.cookies.get('session_id')
    session = api.get_session_with_id(session_id)

    authorization_url = session['oauth_url']
    print(f'we redirect to this URL and authorize the app:\n{authorization_url}\n')

    #after we authorize, we will go to /authorization_code page automaticaly
    # (its configured in the Garmin app we set app in their site)
    return redirect(authorization_url, 302)

stress_data=[]

@app.route('/authorization_code')
def authorization_code():
    global session_id
    global stress_data
    # The service provider has redirected the user back to this route,
    # including the oauth_verifier as a query parameter.

    #get the users session
    #session_id = request.cookies.get('session_id')
    print("1")
    print(session_id)
    session = api.get_session_with_id(session_id)

    #we get the verifier from the url
    oauth_verifier = request.args.get('oauth_verifier')

    #getting our requests tokens back
    request_token = session['req_token']
    request_token_secret = session['req_token_secret']

    oauth = OAuth1Session(CLIENT_ID,
                          client_secret=CLIENT_SECRET,
                          resource_owner_key=request_token,
                          resource_owner_secret=request_token_secret,
                          verifier=oauth_verifier)

    # Exchange the authorized request token for an access token
    access_token = oauth.fetch_access_token('https://connectapi.garmin.com/oauth-service/oauth/access_token')

    # update the user session with the access token
    api.update_session(session_id=session_id,
                       data={'acc_token': access_token['oauth_token'],
                             'acc_token_secret': access_token['oauth_token_secret']} )
    #TODO: insert acces token to database
    print(f"Access Token: {access_token['oauth_token']}")
    print(f"Access Token Secret: {access_token['oauth_token_secret']}")

    #now we can use the Health API endpoints using this token to get the users data from garmins server :)
    #I added a function that does that - just insert some endpoint address to complete the url
    # (its in the 60 pages documents)
    #how bah dahhh
    early = datetime.now(timezone.utc) - timedelta(hours=24, minutes=0)
    some_data = request_data("stressDetails", access_token=access_token['oauth_token'],
                 access_token_secret=access_token['oauth_token_secret'],
                 upload_start=early, upload_end=datetime.today(), is_backfill=False)

    print("check")

    stress_data=list( some_data[-1]['timeOffsetBodyBatteryValues'].values())
    print("stress DATTTTTA ARE COMIIING")
    print( stress_data )


    #TODO: return the participant back to the application
    return f"Access token obtained and printed. Here is the session: {api.get_session_with_id(session_id)}\n\n" \
           f"Here is an example of some userData: {some_data}"


def request_permissions( access_token, access_token_secret):
    # Create an OAuth1 session
    garmin = OAuth1Session(CLIENT_ID,
                           client_secret=CLIENT_SECRET,
                           resource_owner_key=access_token,
                           resource_owner_secret=access_token_secret)

    # Make a GET request to the Garmin Health API
    url = f'https://apis.garmin.com/wellness-api/rest/user/permissions'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


    response = garmin.get(url, headers=headers)

    # Print the response
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Request failed with status {response.status_code}")
        print(response.text)



def request_data(endpoint, access_token, access_token_secret, upload_start, upload_end, is_backfill):
    # Create an OAuth1 session
    garmin = OAuth1Session(CLIENT_ID,
                           client_secret=CLIENT_SECRET,
                           resource_owner_key=access_token,
                           resource_owner_secret=access_token_secret)

    # Make a GET request to the Garmin Health API
    if is_backfill:
        url = f'https://apis.garmin.com/wellness-api/rest/backfill/{endpoint}'
    else:
        url = f'https://apis.garmin.com/wellness-api/rest/{endpoint}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    if is_backfill:
        params = {
            'summaryStartTimeInSeconds': int(upload_start.timestamp()),
            'summaryEndTimeInSeconds': int(upload_end.timestamp())
        }
    else:
        params = {
            'uploadStartTimeInSeconds': int(upload_start.timestamp()),
            'uploadEndTimeInSeconds':int(upload_end.timestamp())
        }

    response = garmin.get(url, params=params, headers=headers)

    # Print the response
    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Request failed with status {response.status_code}")
        print(response.text)
        return response.text

def request_user_information(access_token, access_token_secret, id):
    # Create an OAuth1 session
    garmin = OAuth1Session(CLIENT_ID,
                           client_secret=CLIENT_SECRET,
                           resource_owner_key=access_token,
                           resource_owner_secret=access_token_secret)

    # Make a GET request to the Garmin Health API
    url = f'https://apis.garmin.com/wellness-api/rest/user/id'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


    response = garmin.get(url, headers=headers)

    # Print the response
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Request failed with status {response.status_code}")
        print(response.text)



if __name__ == "__main__":
    app.run(debug=True)



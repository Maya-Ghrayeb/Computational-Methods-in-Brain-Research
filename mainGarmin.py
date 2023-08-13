from datetime import datetime, timedelta

from flask import Flask, redirect, request, render_template
import urllib.parse
from requests_oauthlib import OAuth1Session
import binascii
import os

# These would be provided by Garmin when you register your application
from schonbergAPI import SchonbergLabAPI

CLIENT_ID = '9d686456-8811-4713-bd20-56c96a51792d'
CLIENT_SECRET = 'MsmgnsdocGWYBzho5hAxHNedDKYIcvtaRKr'
REDIRECT_URI = 'http://localhost:5000/authbborization_code'

# URL endpoints provided in Garmin's API documentation
AUTHORIZATION_URL = 'https://connect.garmin.com/oauthConfirm'
TOKEN_URL = 'https://connect.garmin.com/oauth2/token'

app = Flask(__name__)

worker_key = "3377bab2c0e5b030d36fdc37f6d0d6dd1e73a92b7fb505fbfef6138daccf09be0b57699443554587a92a7a1261991a801e173af8bd1d16c15b58351aa7feeae5"
api = SchonbergLabAPI(worker_key)
#session_id = api.add_new_session(data={})['_id']
session_id=None

@app.route('/submit_id', methods=['POST'])
def submit_id():
    global session_id
    participant_id = request.form.get('participantID')

    # Create a new session for the participant and include relevant data
    session_data = {'participant_id': participant_id}

    # Add the new session to the API
    new_session = api.add_new_session(data=session_data)

    session_id = new_session['_id']  # Get the session ID from the created session

    # Retrieve the session data using the session ID and print the participant ID
    retrieved_session = api.get_session_with_id(session_id)
    print(f"Participant ID in the session: {retrieved_session['participant_id']}") # to make sure it was saved in the api

    return "Participant ID saved successfully!"


@app.route('/first_page')
def first_page():

    return render_template('welcome.html')

"""""
@app.route('/lets_test')
def test_page():
    #TODO: add welcome page for the participants - Done 
    #TODO: after collecting the participant number and sending to database, move the user to next page. -Done

    return render_template('index.html')
"""""


@app.route("/tmp")
def tmp():
    collected_id = ""
    #insert to Yonatan's Database
    api.update_session(session_id=session_id, data={'participant_id': collected_id})

@app.route('/to_garmin')
def home():
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
    }
    consumer_key = CLIENT_ID
    consumer_secret = CLIENT_SECRET

    # Step 1: Acquire Unauthorized Request Token and Token Secret (from garmin server)
    request_token_url = "https://connectapi.garmin.com/oauth-service/oauth/request_token"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    r = oauth.fetch_request_token(request_token_url)
    request_token = r.get('oauth_token')
    request_token_secret = r.get('oauth_token_secret')

    #storing our request tokens for later
    os.environ['REQUEST_TOKEN'] = request_token
    os.environ['REQUEST_TOKEN_SECRET'] = request_token_secret



    authorization_url = oauth.authorization_url(AUTHORIZATION_URL)
    print(f'we redirect to this URL and authorize the app:\n{authorization_url}\n')

    #after we authorize, we will go to /authorization_code page automaticaly
    # (its configured in the Garmin app we set app in their site)
    return redirect(authorization_url, 302)



@app.route('/authorization_code')
def authorization_code():
    # The service provider has redirected the user back to this route,
    # including the oauth_verifier as a query parameter.

    #we get the verifier from the url
    oauth_verifier = request.args.get('oauth_verifier')

    # We'll also need the request token details that we stored earlier.
    # These could be stored in a database, or in session data if you're using sessions.
    # In this example, we're retrieving them from environment variables.

    #getting our requests tokens back
    request_token = os.environ.get('REQUEST_TOKEN')
    request_token_secret = os.environ.get('REQUEST_TOKEN_SECRET')

    oauth = OAuth1Session(CLIENT_ID,
                          client_secret=CLIENT_SECRET,
                          resource_owner_key=request_token,
                          resource_owner_secret=request_token_secret,
                          verifier=oauth_verifier)

    # Exchange the authorized request token for an access token
    access_token = oauth.fetch_access_token('https://connectapi.garmin.com/oauth-service/oauth/access_token')

    # At this point you could store the access token details in a database for later use.
    # For this example, we're just printing them.
    #TODO: insert acces token to database
    print(f"Access Token: {access_token['oauth_token']}")
    print(f"Access Token Secret: {access_token['oauth_token_secret']}")

    #now we can use the Health API endpoints using this token to get the users data from garmins server :)
    #I added a function that does that - just insert some endpoint address to complete the url
    # (its in the 60 pages documents)
    early = datetime.today() - timedelta(hours=0, minutes=50)
    request_permissions(access_token=access_token['oauth_token'],
                 access_token_secret=access_token['oauth_token_secret'])
    request_data("userMetrics", access_token=access_token['oauth_token'],
                 access_token_secret=access_token['oauth_token_secret'],
                 upload_start=early, upload_end=datetime.today())

    #TODO: return the participant back to the application
    return "Access token obtained and printed. Check your console."



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



def request_data(endpoint, access_token, access_token_secret, upload_start, upload_end):
    # Create an OAuth1 session
    garmin = OAuth1Session(CLIENT_ID,
                           client_secret=CLIENT_SECRET,
                           resource_owner_key=access_token,
                           resource_owner_secret=access_token_secret)

    # Make a GET request to the Garmin Health API
    url = f'https://apis.garmin.com/wellness-api/rest/{endpoint}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    params = {
        'uploadStartTimeInSeconds': int(upload_start.timestamp()),
        'uploadEndTimeInSeconds': int(upload_end.timestamp())
    }

    response = garmin.get(url, params=params, headers=headers)

    # Print the response
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Request failed with status {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    app.run(debug=True)
    print(api.get_all_sessions())
"""""
    session_id=api.add_new_session(data={'baloon1': '3' , 'baloon2': '5'})['_id']
    print(session_id)
    print(api.get_session_with_id(session_id=session_id))
    print(api.update_session(session_id=session_id, data={'nana': 'baba'}))
    print(api.get_all_sessions()) """




from flask import Flask, render_template
import matplotlib.pyplot as plt
import io
import base64
from schonbergAPI import SchonbergLabAPI
from mainGarmin import worker_key, request_data
from datetime import datetime, timedelta, timezone

api = SchonbergLabAPI(worker_key)


app = Flask(__name__)

def get_base64_graph():
    # Convert Matplotlib graph to base64 for rendering in HTML
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.clf()
    return base64.b64encode(img.read()).decode()

def get_last_session_data():
    # Get all sessions using the original method
    all_sessions = api.get_all_sessions()

    # Check if there are any sessions
    if all_sessions:
        # Initialize variables to hold the last session and session ID
        last_session = None
        last_session_id = ""

        # Iterate through sessions to find the last one
        for session in all_sessions:
            session_id = session.get('_id', '')
            if session_id > last_session_id:  # Assuming session IDs are sortable
                last_session_id = session_id
                last_session = session

        # Check if a last session was found
        if last_session:
            # Extract session ID from the last session
            session_id = last_session.get('_id', '')

            # Fetch data associated with the session_id using the new function
            session_data = api.get_session_with_id(session_id)

            # Check if data was successfully retrieved
            if session_data:
                # Add the lines to request stress data here
                early = datetime.now(timezone.utc) - timedelta(hours=24, minutes=0)
                some_data = request_data("stressDetails", access_token=session_data['acc_token'],
                                         access_token_secret=session_data['acc_token_secret'],
                                         upload_start=early, upload_end=datetime.today(), is_backfill=False)
                stress_data = list(some_data[-1]['timeOffsetBodyBatteryValues'].values())

                # Print the stress data for verification
                print("Stress Data:")
                print(stress_data)
                return stress_data
            else:
                # Handle the case where data retrieval fails
                return None
        else:
            # Handle the case where no last session was found
            return None
    else:
        # Handle the case where there are no sessions
        return None

@app.route('/app')
def dashboard():
    last_session_data = get_last_session_data()

    # Create a stress data graph
    plt.plot(last_session_data)
    plt.xlabel('Time')
    plt.ylabel('Stress Level')
    plt.title('Stress Data Graph')
    stress_graph = get_base64_graph()

    return render_template('dashboard.html', stress_graph=stress_graph)


if __name__ == '__main__':
    # Get the data from the last session
    last_session_data = get_last_session_data()

    if last_session_data:
        # You can use last_session_data as needed in your main script
        print("Data from the last session in the main script:")
        print(last_session_data)


    # Start the Flask app
    app.run(debug=True, port=5001)









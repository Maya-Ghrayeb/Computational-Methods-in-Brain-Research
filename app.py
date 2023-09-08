from typing import Optional, Any, Dict

from flask import Flask, render_template
import matplotlib.pyplot as plt
import io
import base64
from schonbergAPI import SchonbergLabAPI
from mainGarmin import worker_key, request_data
from datetime import datetime, timedelta, timezone
import matplotlib.patches as mpatches

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
    data=[]
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
                stress_data = list(some_data[-1]['timeOffsetStressLevelValues'].values())
                bodyBattery_data = list(some_data[-1]['timeOffsetBodyBatteryValues'].values())
                data.append(stress_data)
                data.append(bodyBattery_data)

                # Print the stress data for verification
                print("Stress Data:")
                print(stress_data)
                return data
            else:
                # Handle the case where data retrieval fails
                return None
        else:
            # Handle the case where no last session was found
            return None
    else:
        # Handle the case where there are no sessions
        return None

def get_bart_data(participant_id) -> Optional[Dict[str, Any]]:
    # Get all sessions using the original method
    all_sessions = api.get_all_sessions()

    # Check if there are any sessions
    if all_sessions:
        # Iterate through sessions to find the correct one
        for session in all_sessions[::-1]:
            if 'email' not in session or session['email'] != participant_id:
                continue
            return session
        return None


@app.route('/')
def dashboard():
    last_session_data_stress = get_last_session_data()[0]
    last_session_data_battery = get_last_session_data()[1]


    # Customize x-axis ticks to show specific time values for both graphs
    x_ticks = [0, 10, 20, 30, 40, 50, 60, 70]  # These represent data points
    x_labels = ["10:00", "10:10", "10:20", "10:30", "10:40", "10:50", "11:00", "11:10"]  # Corresponding time labels

    # Create a subplot with two graphs (stress and bodyBattery)
    plt.figure(figsize=(12, 6))

    # Subplot for Stress Data
    plt.subplot(1, 2, 1)
    plt.plot(last_session_data_stress)
    plt.xlabel('Time')
    plt.ylabel('Stress Level')
    plt.title('Stress Data Graph')
    plt.xticks(x_ticks, x_labels)  # Apply custom ticks

    # Subplot for Body Battery Data
    plt.subplot(1, 2, 2)
    plt.plot(last_session_data_battery)
    plt.xlabel('Time')
    plt.ylabel('Body Battery Level')
    plt.title('Body Battery Data Graph')
    plt.xticks(x_ticks, x_labels)  # Apply custom ticks

    # Save the combined graph
    combined_graph = get_base64_graph()

    # Your data

    bart_data = get_bart_data('eas@ew')
    bart_graph= None
    if bart_data is not None:
        # Extracting relevant data
        trial_types = [trial['trialType'] for trial in bart_data['data']]
        sum_of_gains = [trial['sumOfGains'] for trial in bart_data['data']]
        clicks_amount = [trial['clicksAmount'] for trial in bart_data['data']]
        response_times = [trial['responseTimes'] for trial in bart_data['data']]

        # Plotting sum of gains over trials
        plt.figure(figsize=(15, 5))
        plt.subplot(1, 3, 1)
        plt.plot(sum_of_gains, '-o')
        plt.title("Sum of Gains over Trials")
        plt.xlabel("Trial")
        plt.ylabel("Sum of Gains")

        # Bar plot for number of clicks, colored by trial type
        colors = ['blue' if t == 'Pump' else 'red' for t in trial_types]
        plt.subplot(1, 3, 2)
        bars = plt.bar(range(len(clicks_amount)), clicks_amount, color=colors)
        plt.title("Number of Clicks per Trial")
        plt.xlabel("Trial")
        plt.ylabel("Clicks Amount")
        pump_patch = mpatches.Patch(color='blue', label='Pump')
        cashout_patch = mpatches.Patch(color='red', label='CashOut')
        plt.legend(handles=[pump_patch, cashout_patch])

        # Box plot for response times
        plt.subplot(1, 3, 3)
        plt.boxplot(response_times)
        plt.title("Response Times Distribution per Trial")
        plt.xlabel("Trial")
        plt.ylabel("Response Time (ms)")

        bart_graph = get_base64_graph()

    # Render the template with the combined graph
    return render_template('dashboard.html', combined_graph=combined_graph, bart_graph=bart_graph)

if __name__ == '__main__':
    # Get the data from the last session
    last_session_data = get_last_session_data()

    if last_session_data:
        # You can use last_session_data as needed in your main script
        print("Data from the last session in the main script:")
        print(last_session_data)


    # Start the Flask app
    app.run(debug=True, port=5001)









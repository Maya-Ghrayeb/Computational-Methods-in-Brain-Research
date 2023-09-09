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

def get_base64():
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
                early1 = datetime.now(timezone.utc) - timedelta(hours=24, minutes=0)
                stress = request_data("stressDetails", access_token=session_data['acc_token'],
                                         access_token_secret=session_data['acc_token_secret'],
                                         upload_start=early1, upload_end=datetime.today(), is_backfill=False)

                early2 = datetime.now(timezone.utc) - timedelta(hours=24, minutes=0)
                dailies = request_data("dailies", access_token=session_data['acc_token'],
                                         access_token_secret=session_data['acc_token_secret'],
                                         upload_start=early2, upload_end=datetime.today(), is_backfill=False)

                stress_data=[]
                stress_data.append(list(stress[-1]['timeOffsetStressLevelValues'].keys()))
                stress_data.append(list(stress[-1]['timeOffsetStressLevelValues'].values() ))

                battery_data=[]
                battery_data.append(list(stress[-1]['timeOffsetBodyBatteryValues'].keys()))
                battery_data.append(list(stress[-1]['timeOffsetBodyBatteryValues'].values() ))

                heart_data=[]
                heart_data.append(list(dailies[-1]['timeOffsetHeartRateSamples'].keys()))
                heart_data.append(list(dailies[-1]['timeOffsetHeartRateSamples'].values() ))

                data.append(stress_data)
                data.append(battery_data)
                data.append(heart_data)

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

def get_base64_graph(graph_type):
    # Generate the specified graph
    if graph_type == "stress":
        generate_stress_graph()
    elif graph_type == "battery":
        generate_battery_graph()
    elif graph_type == "heart":
        generate_heart_rate_graph()

    # Save the graph as an image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.clf()
    return base64.b64encode(img.read()).decode()


def generate_stress_graph():
    data_stress = get_last_session_data()[0]
    axisX_stress = []
    for x in data_stress[0]:
        axisX_stress.append(int(x) / 60)

    axisY_stress = data_stress[1]

    # Create a line graph for stress data
    plt.figure(figsize=(6, 4))
    plt.plot(axisX_stress, axisY_stress, marker='o', linestyle='-')
    plt.xlabel('Time in minutes')
    plt.ylabel('Stress')
    plt.title('Stress Graph')

    # Save the graph as an image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.read()).decode()

def generate_battery_graph():
    data_battery = get_last_session_data()[1]
    axisX_battery = []
    for x in data_battery[0]:
        axisX_battery.append(int(x) / 60)

    axisY_battery = data_battery[1]

    # Create a line graph for bodyBattery data
    plt.figure(figsize=(6, 4))
    plt.plot(axisX_battery, axisY_battery, marker='o', linestyle='-')
    plt.xlabel('Time in minutes')
    plt.ylabel('Body Battery')
    plt.title('Body Battery Graph')

    # Save the graph as an image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.read()).decode()


def generate_heart_rate_graph():
    data_heart = get_last_session_data()[2]  # Assuming heart rate data is at index 2
    axisX_heart = []
    for x in data_heart[0]:
        axisX_heart.append(int(x) / 60)

    axisY_heart = data_heart[1]

    # Create a line graph for heart rate data
    plt.figure(figsize=(6, 4))
    plt.plot(axisX_heart, axisY_heart, marker='o', linestyle='-')
    plt.xlabel('Time in minutes')
    plt.ylabel('Heart Rate')
    plt.title('Heart Rate Graph')

    # Save the graph as an image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.read()).decode()


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

    # Generate the base64-encoded stress graph
    combined_graph_stress = get_base64_graph("stress")

    # Generate the base64-encoded bodyBattery graph
    combined_graph_battery = get_base64_graph("battery")

    # Generate the base64-encoded heart rate graph
    combined_graph_heart = get_base64_graph("heart")

    bart_data = get_bart_data('eas@ew')
    bart_graph= None


    if bart_data is not None:
        # Extracting relevant data
        trial_types = [trial['trialType'] for trial in bart_data['data']]
        sum_of_gains = [trial['sumOfGains'] for trial in bart_data['data']]
        clicks_amount = [trial['clicksAmount'] for trial in bart_data['data']]
        response_times = [trial['responseTimes'] for trial in bart_data['data']]

        # Plotting sum of gains over trials
        plt.figure(figsize=(12, 4))
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

        bart_graph = get_base64()


        # Render the template with all graphs and show_welcome_sentences value
    return render_template('dashboard.html', combined_graph_stress=combined_graph_stress,
                            combined_graph_battery=combined_graph_battery,
                            combined_graph_heart=combined_graph_heart,
                            bart_graph=bart_graph)


if __name__ == '__main__':
    # Get the data from the last session
    last_session_data = get_last_session_data()

    # Start the Flask app
    app.run(debug=True, port=5001)









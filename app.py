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
    """try:
        combined_graph_stress = get_base64_graph("stress")
    except:
        combined_graph_stress = None
    # Generate the base64-encoded bodyBattery graph
    try:
        combined_graph_battery = get_base64_graph("battery")
    except:
        combined_graph_battery = None
    # Generate the base64-encoded heart rate graph
    try:
        combined_graph_heart = get_base64_graph("heart")
    except:
        combined_graph_heart = None"""
    garmin_data = {
    "summaryType" : "heart_rate",
    "minValue" : 76.65088977600048,
    "maxValue" : 77.41738003186666,
    "avgValue" : 76.07456615593715,
    "epochSummaries" : {
      "0" : 80.38636290212571,
      "5" : 91.36730011221402,
      "10" : 86.4064395955419,
      "15" : 89.45675509853176,
      "20" : 82.23797159132754,
      "25" : 85.11632587940483,
      "30" : 82.25153194233573,
      "35" : 86.29064354294638,
      "40" : 76.48713156127918,
      "45" : 86.6283978603802,
      "50" : 90.56606236710563,
      "55" : 83.46074058517465,
      "60" : 86.07668687052015,
      "65" : 82.59152210340223,
      "70" : 89.42244040924987,
      "75" : 68.51263402548015,
      "80" : 68.37033580610806,
      "85" : 74.9077464213276,
      "90" : 81.78825137534943,
      "95" : 71.55771545559172,
      "100" : 84.30927808053544,
      "105" : 90.01094360572003,
      "110" : 73.9114151513044,
      "115" : 91.63197734649268
    }
  }, {
    "summaryType" : "stress",
    "minValue" : 6.7643463124907655,
    "maxValue" : 38.42659053139397,
    "avgValue" : 34.360464233052866,
    "epochSummaries" : {
      "1" : 7.5504052640147234,
      "6" : 31.109882658053934,
      "11" : 26.452787812353552,
      "16" : 10.936781094525285,
      "21" : 39.885272058658835,
      "26" : 35.39904734753571,
      "31" : 10.514759279883815,
      "36" : 41.32381719141143,
      "41" : 44.235511335074335,
      "46" : 16.388515660611873,
      "51" : 14.28524737676954,
      "56" : 19.043838114372317,
      "61" : 6.232823692649578,
      "66" : 44.07393852937479,
      "71" : 5.868740141874191,
      "76" : 20.825075711954213,
      "81" : 22.029739449332574,
      "86" : 41.13396529012625,
      "91" : 6.388724046785317,
      "96" : 43.9870890710135,
      "101" : 22.24127013516386,
      "106" : 33.94221051802614,
      "111" : 44.319960378752846,
      "116" : 40.34335061558257
    }
  }, {
    "summaryType" : "spo2",
    "minValue" : 98.40746632377889,
    "maxValue" : 97.77467557989797,
    "avgValue" : 97.16299045424532,
    "epochSummaries" : {
      "2" : 97.5692738551119,
      "7" : 98.36902728300977,
      "12" : 98.5586773040966,
      "17" : 98.56478302150734,
      "22" : 98.6213814274824,
      "27" : 98.79373344088714,
      "32" : 98.97255340229184,
      "37" : 98.59098083351043,
      "42" : 97.81069306441441,
      "47" : 97.23019857210254,
      "52" : 97.78749088390413,
      "57" : 98.46088425902936,
      "62" : 98.615991954708,
      "67" : 98.40344993330925,
      "72" : 98.48112786377958,
      "77" : 97.51621147226102,
      "82" : 98.41667941466876,
      "87" : 98.048340077197,
      "92" : 98.31273247287339,
      "97" : 98.89283811417252,
      "102" : 97.7176893567008,
      "107" : 98.25360185647423,
      "112" : 97.09889859226786,
      "117" : 97.04063374258499
    }
  }, {
    "summaryType" : "respiration",
    "minValue" : 10.075251229727042,
    "maxValue" : 14.602011142604443,
    "avgValue" : 11.378683229922574,
    "epochSummaries" : {
      "3" : 13.336003673331854,
      "8" : 14.761521785479284,
      "13" : 11.866712961659388,
      "18" : 13.158559489576705,
      "23" : 13.128361437838432,
      "28" : 10.14586189548006,
      "33" : 12.70155472213908,
      "38" : 13.418105122614975,
      "43" : 11.213726488475466,
      "48" : 12.493519242428981,
      "53" : 12.269193497741007,
      "58" : 10.663261319069225,
      "63" : 14.340696689763467,
      "68" : 11.029227318339995,
      "73" : 13.438835745995789,
      "78" : 11.571710529886646,
      "83" : 14.625803361592174,
      "88" : 10.438312378039624,
      "93" : 11.689824143040907,
      "98" : 13.895512334942625,
      "103" : 10.546706120889821,
      "108" : 10.634301880075999,
      "113" : 13.184910129012021,
      "118" : 12.371290523651028
    }}

    # Extracting data for plotting
    metrics = ["heart_rate", "stress", "spo2", "respiration"]
    colors = ["blue", "red", "green", "purple"]

    plt.figure(figsize=(12, 8))

    for idx, metric in enumerate(metrics):
        for entry in garmin_data:
            if entry["summaryType"] == metric:
                times = list(map(int, entry["epochSummaries"].keys()))
                values = list(entry["epochSummaries"].values())
                plt.subplot(4, 1, idx + 1)
                plt.plot(times, values, marker='o', color=colors[idx], label=metric.replace("_", " ").title())
                plt.ylabel(metric.replace("_", " ").title())
                plt.legend()

    plt.xlabel('Time (Epochs)')
    plt.tight_layout()
    physio_graph = get_base64()
    bart_data = get_bart_data('212')
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
    return render_template('dashboard.html', combined_graph_stress=physio_graph,
                            combined_graph_battery=physio_graph,
                            combined_graph_heart=physio_graph,
                            bart_graph=bart_graph)


if __name__ == '__main__':
    # Get the data from the last session
    #last_session_data = get_last_session_data()

    # Start the Flask app
    app.run(debug=True, port=5001)









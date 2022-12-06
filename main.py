from flask import Flask, render_template, request, abort
import jsonify
import requests
import traceback
import pickle
import numpy as np
import sklearn
from flask_cors import CORS, cross_origin
from sklearn.preprocessing import StandardScaler
from google.cloud import pubsub_v1
from google.api_core import retry
import json
import os
import copy

app = Flask(__name__)
model = pickle.load(open('random_forest_regression_model1.pkl', 'rb'))
PUB_SUB_TOPIC = "product-pubsub"
PUB_SUB_PROJECT = "sainathcloudcomputing"
PUB_SUB_SUBSCRIPTION = "CloudProject-sub"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "sainathcloudcomputing-e7d30401f420.json"
@app.route('/',methods=['GET'])
def Home():
    return render_template('index.html')


standard_to = StandardScaler()
# @app.route("/predict", methods=['POST'])
def predict1(final_dictionary):
    print("Coming here")
    # global final_dictionary
    Fuel_Type_Diesel=0
    # print('Entering')
    
    print('Entering1')
    Year = int(final_dictionary[' year'])
    Present_Price=float(final_dictionary[' present_price'])
    Kms_Driven=int(final_dictionary[' kms'])
    Kms_Driven2=np.log(Kms_Driven)
    Owner=int(final_dictionary[' owner'])
    Fuel_Type_Petrol=final_dictionary[' fuel_type']

    print(Year,Present_Price,Kms_Driven,Kms_Driven2,Owner,Fuel_Type_Petrol,'workingggg')
    if(Fuel_Type_Petrol=='Petrol'):
            Fuel_Type_Petrol=1
            Fuel_Type_Diesel=0
    else:
        Fuel_Type_Petrol=0
        Fuel_Type_Diesel=1
    Year=2021-Year
    Seller_Type_Individual=final_dictionary[' seller_type']
    if(Seller_Type_Individual=='Individual'):
        Seller_Type_Individual=1
    else:
        Seller_Type_Individual=0	
    Transmission_Mannual=final_dictionary[' transmission_type'][:-2]
    if(Transmission_Mannual=='Mannual'):
        Transmission_Mannual=1
    else:
        Transmission_Mannual=0
    prediction=model.predict([[Present_Price,Kms_Driven2,Owner,Year,Fuel_Type_Diesel,Fuel_Type_Petrol,Seller_Type_Individual,Transmission_Mannual]])
    output=round(prediction[0],2)
    print(output,'the output of our model is')
    if output<0:
        print("Coming here less than 0")
        return render_template('index.html',prediction_text="Sorry you cannot sell this car")
    else:
        print("Coming here proper")
        return render_template('index.html',prediction_text="You Can Sell The Car at {} lacs".format(output))
    
    
    
    # final_result = "<style>*{ box-sizing: border-box; -webkit-box-sizing: border-box; -moz-box-sizing: border-box; } body{ font-family: Helvetica; -webkit-font-smoothing: antialiased; background: linear-gradient(#141e30, #243b55); } .table-wrapper{ margin: 10px 70px 70px; box-shadow: 0px 35px 50px rgba( 0, 0, 0, 0.2 ); } .fl-table { border-radius: 5px; font-size: 12px; font-weight: normal; border: none; border-collapse: collapse; width: 100%; max-width: 100%; white-space: nowrap; background-color: white; } .fl-table td, .fl-table th { text-align: center; padding: 8px; } .fl-table td { border-right: 1px solid #f8f8f8; font-size: 12px; } .fl-table thead th { color: #ffffff; background: #4FC3A1; } .fl-table thead th:nth-child(odd) { color: #ffffff; background: #324960; } .fl-table tr:nth-child(even) { background: #F8F8F8; } h2{ text-align: center; font-size: 18px; text-transform: uppercase; letter-spacing: 1px; color: white; padding: 30px 0; }</style>" \
    #                "<div class=\"table-wrapper\">" \
    #                "<h2> Prediction</h2>" \
    #                "<table class=\"fl-table\">" \
    #                "<tr> <th>Year</th> <th>Kms driven</th> " \
    #                "<th>No of previous owners</th> <th>Fuel Type</th> <th>Cost Price</th>  " \
    #                "<th>Transmission Type</th>  <th>Selling Price Prediction</th> </tr> <tr> <td>" + str(
    #     final_dictionary.get("year")) + "</td> <td>" + \
    #                str(final_dictionary.get("kms")) + "</td> <td>" + str(
    #     final_dictionary.get("owner")) + "</td> <td>" + str(final_dictionary.get("fuel_type")) \
    #                + "</td> <td>" + str(final_dictionary.get("present_price")) + "</td> <td>" \
    #                + str(final_dictionary.get("transmission_type")) + "</td>" \
    #                + " <td>" + str(output) + "</td> </tr> <table>" \
    #                                               "</div>"
                                                  
    #     return final_result, 200


def process_payload(message):
    global final_dictionary
    print("message in payload ",message)
    print(type(message.data),'type')
    # message.ack()
    print(str(message),"convert")
    msg=message.data
    msg=str(msg)
    msg=msg.split(',')
    print(msg,'list')
    final_dictionary={}
    for i in msg:
        conv=i.split('=')
        print(conv[1])
        final_dictionary[conv[0]]=conv[1]
    
    del final_dictionary["b'InputDetails [id"]
    print(final_dictionary)
    print("predict", final_dictionary)
    

@app.route("/predict", methods=['GET', 'POST'])
@cross_origin()
def predict():
    consume_payload()
    if not final_dictionary:
        abort(400)
    print("predict", final_dictionary)
    return predict1(final_dictionary)


# consumer function to consume messages from a topics for a given timeout period
# @app.route("/")
def consume_payload():
    try:
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(PUB_SUB_PROJECT, PUB_SUB_SUBSCRIPTION)
        print(f"Listening for messages on {subscription_path}..\n")
        with subscriber:
            print("in subscriber")

            # The subscriber pulls a specific number of messages. The actual
            # number of messages pulled may be smaller than max_messages.
            response = subscriber.pull(
                request={"subscription": subscription_path, "max_messages": 1},
                retry=retry.Retry(deadline=300),
            )
            ack_ids = []
            for received_message in response.received_messages:
                print(f"Received: {received_message.message.data}.")
                ack_ids.append(received_message.ack_id)

            # Acknowledges the received messages so they will not be sent again.
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids}
            )
            print(
                f"Received and acknowledged {len(response.received_messages)} messages from {subscription_path}."
            )

            print("response is ",response)
            process_payload(response.received_messages[0].message)
    except:
        traceback.print_exc()

if __name__=="__main__":
    app.run(debug=True)


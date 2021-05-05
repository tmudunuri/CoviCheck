import smtplib
import requests
import json

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Environment, PackageLoader
import os
import sys

gmail_user = os.environ.get('gmail_user')
gmail_password = os.environ.get('gmail_password')

import argparse
import datetime

def create_cli_args():
    """Creates CLI arguments for the script.

    Returns:
        Populated namespace object with the required arguments.
    """

    # Mandatory arguments
    description = 'Check vaccine availability'
    parser = argparse.ArgumentParser(description=description)

    input_method = parser.add_mutually_exclusive_group(required=True)
    input_method.add_argument('-p','--pincode',
                        type=int,
                        help="""Specify pincode of center
                        (Mandatory)""")

    input_method.add_argument('-d','--district',
                        type=int,
                        help="""Specify district id of center
                        (Mandatory)""")


    # Optional arguments
    parser.add_argument('-e', '--email',
                        type=str,
                        help="""Specify email for notifications
                        (Mandatory).""")

    parser.add_argument('--date',
                        type=str,
                        help="""Specify date
                        (Mandatory).""",
                        default= datetime.date.today().strftime("%d-%m-%Y"))

    parser.add_argument('-v', '--vaccine',
                        type=str,
                        help="""Specify the vaccine brand. (Optional)
                        E.g. COVISHIELD, COVAXIN, SPUTNIK.""",
                        choices=['COVISHIELD', 'COVAXIN', 'SPUTNIK'],
                        default= 'COVISHIELD')

    parser.add_argument('-a', '--age',
                        type=int,
                        help="""Specify the age of the candidate""",
                        default=18)


    return parser.parse_args()

def get_data(args):
    if hasattr(args, 'district'):
        query = {'district_id': args.district, 'date': args.date}
        response = requests.get("https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict", params=query, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'})
    elif hasattr(args, 'pincode') and hasattr(args, 'date'):
        query = {'pincode': args.pincode, 'date': args.date}
        response = requests.get("https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin", params=query, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'})
    if response.status_code != 200:
        raise Exception("Unable to fetch data : " + str(response.status_code))

    return clean_data(args, response)


def clean_data(args, response):
    age_group = 18 if args.age < 45 else 45

    response_data = json.loads(response.text)
    centers = response_data.get('centers')
    if len(centers) == 0:
        raise Exception("No centers found")

    filtered_centers = list()
    for center in centers:
        filtered_sessions = list()
        for session in center['sessions']:
            if session['min_age_limit'] == age_group and session['available_capacity'] > 0:
                if hasattr(args, 'vaccine') and session['vaccine'] == args.vaccine:
                    filtered_sessions.append(session)
                elif not hasattr(args, 'vaccine'):
                    filtered_sessions.append(session)
        # Filter sessions based on availability and age
        center['sessions'] = filtered_sessions
        filtered_centers.append(center)

    # Filter centers with no sessions
    filtered_centers[:] = [center for center in filtered_centers if center['sessions']]
    if len(filtered_centers) == 0:
        raise Exception("Vaccines unavailable")

    cleaned_centers = list()
    for center in filtered_centers:
        center['vaccine_fees'] = [{}] if not hasattr(center, 'vaccine_fees') else center['vaccine_fees'][0]
        center = {key: value for key, value in center.items() if key in ['name', 'address', 'pincode', 'sessions', 'vaccine_fees']}
        temp_sessions = list()
        for session in center['sessions']:
            session = {key: value for key, value in session.items() if key in ['date', 'available_capacity', 'vaccine']}
            temp_sessions.append(session)
        center['sessions'] = temp_sessions

        # Append a Maps search URL
        maps_URL = 'https://www.google.com/maps/search/?api=1'
        maps_query = {'query': center['name'] + ' ' + center['address'] + ' ' + str(center['pincode'])}
        center['location'] = requests.Request('GET', maps_URL, params=maps_query).prepare().url

        cleaned_centers.append(center)
    print("Cleaning Data")
    return sorted(cleaned_centers, key = lambda item: item['name'])



def send_mail(bodyContent):
    """Sends email to user.

    Args:
        bodyContent: (str) The HTML output to be sent
    """
    print("Sending Mail")
    to_email = gmail_user
    from_email = gmail_user
    message = MIMEMultipart()
    message['Subject'] = 'Vaccine Available'
    message['From'] = "Covicheck <{from_email}>"
    message['To'] = to_email

    message.attach(MIMEText(bodyContent, "html"))
    msgBody = message.as_string()

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, gmail_password)
    server.sendmail(from_email, to_email, msgBody)

    server.quit()



env = Environment(
    loader=PackageLoader('covicheck', 'templates')
)


def main(event=None):
    """Driver for the script"""
    try:
        if event:
            args = argparse.Namespace(**event)
            if not hasattr(args, 'date'):
                args.date = datetime.date.today().strftime("%d-%m-%Y")
            if not hasattr(args, 'age'):
                args.age = 18
        else:
            args =  create_cli_args()
        json_data = get_data(args)
        template = env.get_template('child.html')
        output = template.render(data=json_data)
        send_mail(output)
    except Exception as exception:
        print(exception)
        sys.exit(1)

if __name__ == '__main__':
    main()
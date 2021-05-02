#!/usr/bin/env python
import smtplib
import requests
import json

from config import gmail_user, gmail_password

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Environment, PackageLoader
import os

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

    input_method = parser.add_mutually_exclusive_group(required=False)
    input_method.add_argument('-p','--pincode',
                        type=int,
                        help="""Specify pincode of center
                        (Mandatory)""")

    input_method.add_argument('-d','--district',
                        type=int,
                        help="""Specify district id of center
                        (Mandatory)""",
                        default=294)


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

    parser.add_argument('-b', '--brand',
                        type=str,
                        help="""Specify the vaccine brand. (Optional)
                        E.g. covishield, covaxin, sputnik.""",
                        choices=['covishield', 'covaxin', 'sputnik'],
                        default= 'covishield')

    parser.add_argument('-a', '--age',
                        type=int,
                        help="""Specify the age of the candidate""",
                        default=45)


    return parser.parse_args()

def get_data(args):
    if args.district:
        query = {'district_id': args.district, 'date': args.date}
        response = requests.get("https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict", params=query)
    elif args.pincode and args.date:
        query = {'pincode': args.pincode, 'date': args.date}
        response = requests.get("https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin", params=query)
    else:
        return 0
    return clean_data(args, response)


def clean_data(args, response):
    age = 18 if args.age < 45 else 45

    response_data = json.loads(response.text)
    centers = response_data.get('centers')

    filtered_centers = list()
    for center in centers:
        filtered_sessions = list()
        for session in center['sessions']:
            if session['min_age_limit'] == age and session['available_capacity'] > 0:
                filtered_sessions.append(session)
        # Filter sessions based on availability and age
        center['sessions'] = filtered_sessions
        filtered_centers.append(center)

    # Filter centers with no sessions
    filtered_centers[:] = [center for center in filtered_centers if center['sessions']]

    cleaned_centers = list()
    for center in filtered_centers:
        center = {key: value for key, value in center.items() if key in ['name', 'pincode', 'sessions', 'fee_type']}
        temp_sessions = list()
        for session in center['sessions']:
            session = {key: value for key, value in session.items() if key in ['date', 'available_capacity', 'vaccine']}
            temp_sessions.append(session)
        center['sessions'] = temp_sessions

        # Append a Maps search URL
        maps_URL = 'https://www.google.com/maps/search/?api=1'
        maps_query = {'query': center['name'] + ' ' + str(center['pincode'])}
        center['location'] = requests.Request('GET', maps_URL, params=maps_query).prepare().url

        cleaned_centers.append(center)
        
    return sorted(cleaned_centers, key = lambda item: item['name'])



def send_mail(bodyContent):
    """Sends email to user.

    Args:
        bodyContent: (str) The HTML output to be sent
    """
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

def eprint(error='There was an error'):
    """Prints error to stderr.

    Args:
        error: (str) The error to be printed.
    """
    print(error, file=sys.stderr)


def main():
    """Driver for the script"""
    args = create_cli_args()
    json_data = get_data(args)
    template = env.get_template('child.html')
    output = template.render(data=json_data)
    print(output)
    send_mail(output)  
    # except Exception as exception:
    #     eprint(exception)
    #     sys.exit(1)

if __name__ == '__main__':
    main()
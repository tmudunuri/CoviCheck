import base64
import json
from covicheck import covicheck

def covicheck_pubsub(event, context):
    if 'data' in event:
        data_string = base64.b64decode(event['data']).decode('utf-8')
        data = json.loads(data_string)
    else:
        data = event
    try:
        covicheck.main(data)
    except Exception as exception:
        return exception
    print('Complete')


# CoviCheck

> Script consumes Co-WIN Public APIs : [Appointment Availability APIs
](https://apisetu.gov.in/public/marketplace/api/cowin)

Check availability of vaccines in your district / pincode and get notified via email.
## **Instructions**

### Run Locally :
1. Open cloned directory\
```cd CoviCheck```
2. Setup venv\
```python -m venv venv```
3. Activate venv\
```source venv/bin/activate```
4. Install dependencies\
```pip install -r requirements.txt```
5. Export your gmail credentials
```
export gmail_user=<your-email-address>
export gmail_password=<your-app-password>
```
> Follow [Create App Passwords](https://support.google.com/accounts/answer/185833?hl=en)
6. Run script
```python covicheck/covicheck.py <args>```
> See `python covicheck/covicheck.py --help` for usage

### Use GCP Cloud Functions:
- Use Event-Driven Cloud Functions
[Tutorial](https://cloud.google.com/functions/docs/tutorials/pubsub#functions-prepare-environment-python)
*Add email credentials as runtime environment variables*
- Upload zipped source code. See [Specifying dependencies in Python](https://cloud.google.com/functions/docs/writing/specifying-dependencies-python)  
- Use Cloud Scheduler to [Create and configure a cron job](https://cloud.google.com/scheduler/docs/creating#console_1)

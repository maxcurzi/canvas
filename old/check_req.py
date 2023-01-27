import requests

url = "https://35.195.84.144:443/update_pixels"
myobj = {"x": 30, "y": 30, "user": "cippalippa"}
session = requests.Session()
x = requests.post(url, json=myobj, verify=True)

import requests

url = "http://localhost:8000/uploadimage/"
file = {"image": open("tests/image.jpg", "rb")}
resp = requests.post(url, files=file)
print(resp.json())

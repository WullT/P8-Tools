from flask import Flask, request, jsonify, make_response, send_file
import os
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash


USERNAME = "MY_USER"
PASSWORD = "MY_PASSWORD"
INPUT_DIRECTORY = "sample_images"
HOST = "0.0.0.0"
PORT = 8080

class ImageList:
    def __init__(self):
        self.images = []
        self.index = 0

    def load(self, path):
        if not path.endswith("/"):
            path += "/"
            self.images = [
                path + f
                for f in os.listdir(path)
                if os.path.isfile(path + f) and f.endswith(".jpg")
            ]

    def add(self, image):
        self.images.append(image)

    def get(self):
        if self.index >= len(self.images):
            self.index = 0
            print("Reset index")
        image = self.images[self.index]
        print("Get image nr {} out of {}".format(self.index, len(self.images)))
        self.index += 1
        return image


imglist = ImageList()
imglist.load(INPUT_DIRECTORY)

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {USERNAME: generate_password_hash(PASSWORD)}


@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username


@app.route("/", methods=["GET"])
@auth.login_required
def snapshot():
    if request.args.get("action") == "snapshot":
        image = imglist.get()
        return send_file(image, mimetype="image/jpeg")
    if request.args.get("index") is not None:
        imglist.index = int(request.args.get("index"))
        print("Set index to {}".format(imglist.index))

        image = imglist.get()
        return send_file(image, mimetype="image/jpeg")
    return "Error"


app.run(host=HOST, port=PORT, debug=True)

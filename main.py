from flask import Flask, json
from pymongo import MongoClient

USER_KEYS : []
URL = "mongodb://grupo32:grupo32@gray.ing.puc.cl/grupo32?authSource=admin"
client = MongoClient(URL)
db = client["grupo32"]
app = Flask(__name__)
@app.route("/")
def home():
    return "<h1>wololo</h1>"

@app.route("/users")
def get_users():
    users = list(db.usuarios.find({}, {"_id": 0}))
    print(users)
    return json.jsonify(users)

@app.route("/users/<int:uid>")
def get_user(uid):
    user = list(db.usuarios.find({"uid": uid}, {"_id": 0}))
    print(user)
    return json.jsonify(user)

@app.route("/users", methods=['POST'])
def create_user():
    print(request.json)
    data = {key: request.json[key] for key in USER_KEYS}
    result = usuarios.insert_one(data)
    return json.jsonify({"success": True})

if __name__ == "__main__":
    #app.run()
    app.run(debug=True)


import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

db_path = os.path.join(os.path.dirname(__file__), 'HouseSalesSeattle.db')
connection = sqlite3.connect(db_path, check_same_thread=False)
cursor = connection.cursor()

socketio = SocketIO(app, cors_allowed_origins="*")

bids = [
    {"name": "Albin", "amount": 2500000},
    {"name": "Hudeyfi", "amount": 2600000}
]

@app.route("/")
def home():
    return send_from_directory(".", "husindex.html")


@app.route("/test-db")
def test_db():
    cursor.execute("SELECT * FROM HouseSalesSeattle LIMIT 5")
    rows = cursor.fetchall()
    return jsonify(rows)


@app.route("/api/properties")
def get_properties():
    zip_code = request.args.get("zip_code")
    min_bedrooms = request.args.get("min_bedrooms", type=int)

    query = """
        SELECT 
            SalesID,
            Image,
            zip_code,
            AdjSalePrice,
            Bedrooms,
            Bathrooms,
            SqMTotLiving
        FROM HouseSalesSeattle
        WHERE 1=1
    """

    params = []

    if zip_code:
        query += " AND zip_code = ?"
        params.append(zip_code)

    if min_bedrooms is not None:
        query += " AND Bedrooms >= ?"
        params.append(min_bedrooms)

    query += " LIMIT 380"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    properties = []
    for row in rows:
        properties.append({
            "SalesID": row[0],
            "Image": row[1],
            "zip_code": row[2],
            "AdjSalePrice": row[3],
            "Bedrooms": row[4],
            "Bathrooms": row[5],
            "SqMTotLiving": row[6]
        })

    return jsonify(properties)

@app.route("/api/bids")
def get_bids():
    return jsonify(bids)


@socketio.on("connect")
def handle_connect():
    emit("update_bids", bids)


@socketio.on("new_bid")
def handle_new_bid(data):
    name = data.get("name")
    amount = data.get("amount")

    if name and amount:
        bid = {
            "name": name,
            "amount": int(amount)
        }

        bids.append(bid)

        socketio.emit("update_bids", bids)


if __name__ == "__main__":
    socketio.run(app, debug=True)

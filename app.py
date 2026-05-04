import os
import time
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

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=12, type=int)

    if page < 1:
        page = 1

    if per_page < 1:
        per_page = 12

    if per_page > 15:
        per_page = 15

    offset = (page - 1) * per_page

    base_query = """
        FROM HouseSalesSeattle
        WHERE 1=1
    """

    params = []

    if zip_code:
        base_query += " AND zip_code = ?"
        params.append(zip_code)

    if min_bedrooms is not None:
        base_query += " AND Bedrooms >= ?"
        params.append(min_bedrooms)

    count_query = "SELECT COUNT(*) " + base_query

    data_query = """
        SELECT 
            SalesID,
            Image,
            zip_code,
            AdjSalePrice,
            Bedrooms,
            Bathrooms,
            SqMTotLiving
    """ + base_query + """
        ORDER BY SalesID
        LIMIT ? OFFSET ?
    """

    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    cursor.execute(data_query, params + [per_page, offset])
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

    return jsonify({
        "properties": properties,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page
    })

@app.route("/api/bids")
def get_bids():
    return jsonify(bids)


@app.route("/api/price-per-zip")
def price_per_zip():
    cursor.execute("""
        SELECT zip_code, AVG(AdjSalePrice)
        FROM HouseSalesSeattle
        GROUP BY zip_code
        LIMIT 10
    """)

    rows = cursor.fetchall()

    data = {
        "labels": [row[0] for row in rows],
        "values": [row[1] for row in rows]
    }

    return jsonify(data)

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
            "amount": int(amount),
            "time": time.time()
        }

        bids.append(bid)

        socketio.emit("update_bids", bids)


if __name__ == "__main__":
    socketio.run(app, debug=True)

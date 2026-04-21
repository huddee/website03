import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

db_path = os.path.join(os.path.dirname(__file__), 'HouseSalesSeattle.db')
connection = sqlite3.connect(db_path, check_same_thread=False)
cursor = connection.cursor()

@app.route("/")
def home():
    return "Flask server is running and database is connected!"

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

if __name__ == "__main__":
    app.run(debug=True)
    


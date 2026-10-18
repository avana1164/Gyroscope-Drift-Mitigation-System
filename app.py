from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/api/test", methods=["POST"])
def test():
    print("Received:", request.json)

    return jsonify({
        "status": "success",
        "message": "Arduino reached Flask!"
    })

app.run(host="0.0.0.0", port=5001)

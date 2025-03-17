import socket
import json
from flask import Flask, jsonify

app = Flask(__name__)

# Setup UDP socket to listen for data
serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverAddressPort = ("127.0.0.1", 5052)
serverSock.bind(serverAddressPort)

print("Server is listening on", serverAddressPort)

# Variable to hold the latest received data
latest_data = None

# Function to listen for UDP messages
def listen_for_udp():
    global latest_data
    while True:
        data, addr = serverSock.recvfrom(1024)  # Buffer size is 1024 bytes
        try:
            message = json.loads(data.decode())  # Decode the received data
            latest_data = message  # Store the latest data
            print(f"Received data: {message}")
        except json.JSONDecodeError:
            print("Failed to decode JSON")

# Start the UDP listening in a separate thread
import threading
udp_thread = threading.Thread(target=listen_for_udp, daemon=True)
udp_thread.start()

# Endpoint to expose the received data to Postman via HTTP
@app.route('/received-data', methods=['GET'])
def get_received_data():
    if latest_data:
        return jsonify(latest_data)
    else:
        return jsonify({"message": "No data received yet"}), 404

if __name__ == '__main__':
    app.run(port=5000)

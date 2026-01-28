#!/usr/bin/env python3
"""
Participant (Resource Manager) for 2PC and 3PC
"""

import argparse
import sys
import time
from flask import Flask, request, jsonify
from enum import Enum
from threading import Lock

class TransactionState(Enum):
    INIT = "INIT"
    READY = "READY"
    PRECOMMITTED = "PRECOMMITTED"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"

class Participant:
    def __init__(self, node_id, port):
        self.node_id = node_id
        self.port = port
        self.transactions = {}
        self.resources = {"x": 100}
        self.lock = Lock()
        
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [Participant {self.node_id}] {message}")
        sys.stdout.flush()
    
    def validate_operation(self, tx_id, operation):
        self.log(f"{tx_id} Validating operation: {operation}")
        if "x" in operation:
            if self.resources["x"] + (-10) >= 0:
                return True
        return True
    
    def handle_prepare(self, tx_id, operation):
        self.log(f"{tx_id} Received PREPARE")
        self.transactions[tx_id] = TransactionState.INIT
        
        if self.validate_operation(tx_id, operation):
            self.transactions[tx_id] = TransactionState.READY
            self.log(f"{tx_id} VOTE-YES")
            return "YES"
        else:
            self.transactions[tx_id] = TransactionState.ABORTED
            self.log(f"{tx_id} VOTE-NO")
            return "NO"
    
    def handle_decision(self, tx_id, decision):
        self.log(f"{tx_id} Received {decision}")
        
        with self.lock:
            if decision == "COMMIT":
                self.resources["x"] -= 10
                self.transactions[tx_id] = TransactionState.COMMITTED
                self.log(f"{tx_id} COMMIT (x = {self.resources['x']})")
            else:
                self.transactions[tx_id] = TransactionState.ABORTED
                self.log(f"{tx_id} ABORT")
        
        return "ACK"
    
    def handle_can_commit(self, tx_id, operation):
        self.log(f"{tx_id} Received CAN-COMMIT")
        self.transactions[tx_id] = TransactionState.INIT
        
        if self.validate_operation(tx_id, operation):
            self.log(f"{tx_id} Response: YES")
            return "YES"
        else:
            self.log(f"{tx_id} Response: NO")
            return "NO"
    
    def handle_pre_commit(self, tx_id):
        self.log(f"{tx_id} Received PRE-COMMIT")
        self.transactions[tx_id] = TransactionState.PRECOMMITTED
        self.log(f"{tx_id} State: PRECOMMITTED")
        return "ACK"
    
    def handle_do_commit(self, tx_id):
        self.log(f"{tx_id} Received DO-COMMIT")
        
        with self.lock:
            self.resources["x"] -= 10
            self.transactions[tx_id] = TransactionState.COMMITTED
            self.log(f"{tx_id} COMMIT (x = {self.resources['x']})")
        
        return "ACK"
    
    def get_state(self, tx_id):
        return self.transactions.get(tx_id, TransactionState.INIT)

def create_app(participant):
    app = Flask(__name__)
    
    @app.route('/prepare', methods=['POST'])
    def prepare():
        data = request.json
        tx_id = data['tx_id']
        operation = data['operation']
        vote = participant.handle_prepare(tx_id, operation)
        return jsonify({"vote": vote})
    
    @app.route('/decision', methods=['POST'])
    def decision():
        data = request.json
        tx_id = data['tx_id']
        decision = data['decision']
        result = participant.handle_decision(tx_id, decision)
        return jsonify({"result": result})
    
    @app.route('/can_commit', methods=['POST'])
    def can_commit():
        data = request.json
        tx_id = data['tx_id']
        operation = data['operation']
        vote = participant.handle_can_commit(tx_id, operation)
        return jsonify({"vote": vote})
    
    @app.route('/pre_commit', methods=['POST'])
    def pre_commit():
        data = request.json
        tx_id = data['tx_id']
        result = participant.handle_pre_commit(tx_id)
        return jsonify({"result": result})
    
    @app.route('/do_commit', methods=['POST'])
    def do_commit():
        data = request.json
        tx_id = data['tx_id']
        result = participant.handle_do_commit(tx_id)
        return jsonify({"result": result})
    
    @app.route('/state/<tx_id>', methods=['GET'])
    def get_state(tx_id):
        state = participant.get_state(tx_id)
        return jsonify({"tx_id": tx_id, "state": state.value})
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({"status": "healthy", "node_id": participant.node_id})
    
    return app

def main():
    parser = argparse.ArgumentParser(description='Transaction Participant')
    parser.add_argument('--id', required=True, help='Participant ID')
    parser.add_argument('--port', type=int, required=True, help='Port number')
    
    args = parser.parse_args()
    
    participant = Participant(args.id, args.port)
    participant.log(f"Started on port {args.port}")
    
    app = create_app(participant)
    app.run(host='0.0.0.0', port=args.port, debug=False)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Coordinator for 2PC and 3PC Distributed Transactions with HTTP Server
"""

import argparse
import time
import requests
import sys
from enum import Enum
from threading import Lock, Thread
from flask import Flask, request, jsonify

class TransactionState(Enum):
    INIT = "INIT"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    COMMITTING = "COMMITTING"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"
    PRECOMMITTING = "PRECOMMITTING"

class Coordinator:
    def __init__(self, node_id, port, participants, protocol="2PC"):
        self.node_id = node_id
        self.port = port
        self.participants = participants
        self.protocol = protocol
        self.transactions = {}
        self.votes = {}
        self.lock = Lock()
        
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [Coordinator {self.node_id}] {message}")
        sys.stdout.flush()
    
    def start_transaction_2pc(self, tx_id, operation):
        """Execute 2PC protocol"""
        self.log(f"{tx_id} INIT")
        self.transactions[tx_id] = TransactionState.INIT
        self.votes[tx_id] = {}
        
        # Phase 1: PREPARE
        self.log(f"{tx_id} PREPARE")
        self.transactions[tx_id] = TransactionState.PREPARING
        
        all_voted_yes = True
        timeout = 5
        
        for part_id, host, port in self.participants:
            try:
                url = f"http://{host}:{port}/prepare"
                data = {"tx_id": tx_id, "operation": operation}
                self.log(f"{tx_id} Sending PREPARE to {part_id} ({host}:{port})")
                
                response = requests.post(url, json=data, timeout=timeout)
                vote = response.json().get("vote", "NO")
                
                self.votes[tx_id][part_id] = vote
                self.log(f"{tx_id} Received VOTE-{vote} from {part_id}")
                
                if vote != "YES":
                    all_voted_yes = False
                    
            except Exception as e:
                self.log(f"{tx_id} ERROR: Participant {part_id} failed: {e}")
                self.votes[tx_id][part_id] = "NO"
                all_voted_yes = False
        
        # Phase 2: COMMIT or ABORT
        if all_voted_yes:
            self.log(f"{tx_id} GLOBAL-COMMIT")
            self.transactions[tx_id] = TransactionState.COMMITTING
            decision = "COMMIT"
        else:
            self.log(f"{tx_id} GLOBAL-ABORT")
            self.transactions[tx_id] = TransactionState.ABORTED
            decision = "ABORT"
        
        # Send decision to all participants
        for part_id, host, port in self.participants:
            try:
                url = f"http://{host}:{port}/decision"
                data = {"tx_id": tx_id, "decision": decision}
                response = requests.post(url, json=data, timeout=timeout)
                self.log(f"{tx_id} Sent {decision} to {part_id}")
            except Exception as e:
                self.log(f"{tx_id} ERROR: Failed to send decision to {part_id}: {e}")
        
        if decision == "COMMIT":
            self.transactions[tx_id] = TransactionState.COMMITTED
            self.log(f"{tx_id} COMMITTED")
        else:
            self.log(f"{tx_id} ABORTED")
        
        return decision
    
    def start_transaction_3pc(self, tx_id, operation):
        """Execute 3PC protocol"""
        self.log(f"{tx_id} INIT")
        self.transactions[tx_id] = TransactionState.INIT
        self.votes[tx_id] = {}
        
        # Phase 1: CanCommit
        self.log(f"{tx_id} CAN-COMMIT")
        all_can_commit = True
        timeout = 5
        
        for part_id, host, port in self.participants:
            try:
                url = f"http://{host}:{port}/can_commit"
                data = {"tx_id": tx_id, "operation": operation}
                self.log(f"{tx_id} Sending CAN-COMMIT to {part_id}")
                
                response = requests.post(url, json=data, timeout=timeout)
                vote = response.json().get("vote", "NO")
                
                self.votes[tx_id][part_id] = vote
                self.log(f"{tx_id} Received {vote} from {part_id}")
                
                if vote != "YES":
                    all_can_commit = False
                    
            except Exception as e:
                self.log(f"{tx_id} ERROR: {part_id} failed: {e}")
                self.votes[tx_id][part_id] = "NO"
                all_can_commit = False
        
        if not all_can_commit:
            self.log(f"{tx_id} GLOBAL-ABORT (Phase 1)")
            self.transactions[tx_id] = TransactionState.ABORTED
            for part_id, host, port in self.participants:
                try:
                    url = f"http://{host}:{port}/decision"
                    requests.post(url, json={"tx_id": tx_id, "decision": "ABORT"}, timeout=timeout)
                except:
                    pass
            return "ABORT"
        
        # Phase 2: PreCommit
        self.log(f"{tx_id} PRE-COMMIT")
        self.transactions[tx_id] = TransactionState.PRECOMMITTING
        
        for part_id, host, port in self.participants:
            try:
                url = f"http://{host}:{port}/pre_commit"
                data = {"tx_id": tx_id}
                self.log(f"{tx_id} Sending PRE-COMMIT to {part_id}")
                response = requests.post(url, json=data, timeout=timeout)
                self.log(f"{tx_id} {part_id} acknowledged PRE-COMMIT")
            except Exception as e:
                self.log(f"{tx_id} ERROR: {part_id} failed at PRE-COMMIT: {e}")
        
        # Phase 3: DoCommit
        self.log(f"{tx_id} DO-COMMIT")
        self.transactions[tx_id] = TransactionState.COMMITTING
        
        for part_id, host, port in self.participants:
            try:
                url = f"http://{host}:{port}/do_commit"
                data = {"tx_id": tx_id}
                response = requests.post(url, json=data, timeout=timeout)
                self.log(f"{tx_id} {part_id} committed")
            except Exception as e:
                self.log(f"{tx_id} ERROR: {part_id} failed at DO-COMMIT: {e}")
        
        self.transactions[tx_id] = TransactionState.COMMITTED
        self.log(f"{tx_id} COMMITTED (3PC)")
        return "COMMIT"

def create_app(coordinator):
    app = Flask(__name__)
    
    @app.route('/transaction', methods=['POST'])
    def handle_transaction():
        data = request.json
        tx_id = data.get('tx_id')
        operation = data.get('operation')
        protocol = data.get('protocol', coordinator.protocol)
        
        if not tx_id or not operation:
            return jsonify({"error": "Missing tx_id or operation"}), 400
        
        # Execute in background thread to not block HTTP response
        def execute():
            if protocol == "3PC":
                result = coordinator.start_transaction_3pc(tx_id, operation)
            else:
                result = coordinator.start_transaction_2pc(tx_id, operation)
        
        thread = Thread(target=execute)
        thread.start()
        
        return jsonify({"status": "started", "tx_id": tx_id})
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({"status": "healthy", "node_id": coordinator.node_id})
    
    return app

def main():
    parser = argparse.ArgumentParser(description='Transaction Coordinator')
    parser.add_argument('--id', required=True, help='Coordinator ID')
    parser.add_argument('--port', type=int, required=True, help='Port number')
    parser.add_argument('--participants', required=True, 
                       help='Comma-separated: B:host:port,C:host:port')
    parser.add_argument('--protocol', default='2PC', choices=['2PC', '3PC'])
    
    args = parser.parse_args()
    
    participants = []
    for part in args.participants.split(','):
        parts = part.split(':')
        if len(parts) == 3:
            participants.append((parts[0], parts[1], int(parts[2])))
    
    coordinator = Coordinator(args.id, args.port, participants, args.protocol)
    coordinator.log(f"Started with protocol {args.protocol}")
    coordinator.log(f"Participants: {[p[0] for p in participants]}")
    
    app = create_app(coordinator)
    coordinator.log("HTTP server starting...")
    app.run(host='0.0.0.0', port=args.port, debug=False)

if __name__ == "__main__":
    main()

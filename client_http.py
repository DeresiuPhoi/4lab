#!/usr/bin/env python3
"""
Client to trigger distributed transactions via HTTP
"""

import argparse
import requests
import sys

def trigger_transaction(coordinator_host, coordinator_port, tx_id, operation, protocol):
    print(f"\n{'='*60}")
    print(f"Triggering Transaction: {tx_id}")
    print(f"Operation: {operation}")
    print(f"Protocol: {protocol}")
    print(f"Coordinator: {coordinator_host}:{coordinator_port}")
    print(f"{'='*60}\n")
    
    try:
        url = f"http://{coordinator_host}:{coordinator_port}/transaction"
        data = {
            "tx_id": tx_id,
            "operation": operation,
            "protocol": protocol
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Transaction initiated: {result}")
            print(f"\nCheck coordinator and participant logs for details.\n")
            return True
        else:
            print(f"✗ Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"✗ ERROR: Cannot connect to coordinator at {coordinator_host}:{coordinator_port}")
        print("  Make sure the coordinator is running!")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Transaction Client')
    parser.add_argument('--coordinator', required=True, 
                       help='Coordinator address (host:port)')
    parser.add_argument('--tx', required=True, help='Transaction ID')
    parser.add_argument('--op', required=True, help='Operation (e.g., "x=-10")')
    parser.add_argument('--protocol', default='2PC', choices=['2PC', '3PC'],
                       help='Protocol to use')
    
    args = parser.parse_args()
    
    host, port = args.coordinator.split(':')
    port = int(port)
    
    success = trigger_transaction(host, port, args.tx, args.op, args.protocol)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

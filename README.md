# Distributed Transactions Lab - 2PC & 3PC

## Lab Information
- **Nodes**: 3 EC2 instances (1 coordinator + 2 participants)
- **Protocols**: Two-Phase Commit (2PC) and Three-Phase Commit (3PC)
- **Key Pair**: transaction
- **Security Group**: Ports 8000-8010 (TCP), Port 22 (SSH)

## EC2 Instances
```
Coordinator: 3.95.212.5
Participant B: 184.73.13.182
Participant C: 100.48.82.58
```

---

## STEP-BY-STEP DEPLOYMENT GUIDE

### Step 1: Connect to EC2 Instances

Open **3 terminal windows** (one for each instance):

**Terminal 1 - Coordinator:**
```bash
ssh -i transaction.pem ubuntu@3.95.212.5
```

**Terminal 2 - Participant B:**
```bash
ssh -i transaction.pem ubuntu@184.73.13.182
```

**Terminal 3 - Participant C:**
```bash
ssh -i transaction.pem ubuntu@100.48.82.58
```

---

### Step 2: Setup Each Instance

**Run on ALL 3 instances:**

```bash
# Update system
sudo apt-get update

# Install Python and pip
sudo apt-get install -y python3 python3-pip

# Install required libraries
pip3 install flask requests

# Create working directory
mkdir -p ~/distributed-tx
cd ~/distributed-tx
```

---

### Step 3: Upload Code Files

**Upload these files to ALL 3 instances:**
- `participant.py`

**Upload these files to Coordinator ONLY:**
- `coordinator_server.py`
- `client_http.py`

**Using SCP from your local machine:**

```bash
# Upload to Coordinator
scp -i transaction.pem coordinator_server.py client_http.py ubuntu@3.95.212.5:~/distributed-tx/

# Upload to Participant B
scp -i transaction.pem participant.py ubuntu@184.73.13.182:~/distributed-tx/

# Upload to Participant C
scp -i transaction.pem participant.py ubuntu@100.48.82.58:~/distributed-tx/
```

---

### Step 4: Start the System

**Start in this order:**

**1. Start Participant B (Terminal 2):**
```bash
cd ~/distributed-tx
python3 participant.py --id B --port 8001
```

**2. Start Participant C (Terminal 3):**
```bash
cd ~/distributed-tx
python3 participant.py --id C --port 8002
```

**3. Start Coordinator (Terminal 1):**
```bash
cd ~/distributed-tx
python3 coordinator_server.py --id COORD --port 8000 \
  --participants B:184.73.13.182:8001,C:100.48.82.58:8002 \
  --protocol 2PC
```

---

## RUNNING TEST SCENARIOS


**From coordinator terminal (Terminal 1), open a new SSH session:**
```bash
ssh -i transaction.pem ubuntu@3.95.212.5
cd ~/distributed-tx
python3 client_http.py --coordinator localhost:8000 --tx TX001 --op "x=-10" --protocol 2PC
```

**Expected output:**
```
[Coordinator] TX001 INIT
[Coordinator] TX001 PREPARE
[Participant B] TX001 Received PREPARE
[Participant B] TX001 VOTE-YES
[Participant C] TX001 Received PREPARE
[Participant C] TX001 VOTE-YES
[Coordinator] TX001 GLOBAL-COMMIT
[Coordinator] TX001 COMMITTED
```

---

### Test 2: Failed Transaction - Participant Timeout 

**Stop Participant C (Ctrl+C in Terminal 3)**

**Trigger transaction:**
```bash
python3 client_http.py --coordinator localhost:8000 --tx TX002 --op "x=-10" --protocol 2PC
```

**Expected:**
- Coordinator times out waiting for Participant C
- Transaction ABORTS



**Restart Participant C after test**

---

### Test 3: Coordinator Crash - Blocking

This demonstrates the **blocking problem** in 2PC.

**Step 1:** Start a transaction but don't let it complete
**Step 2:** Kill coordinator (Ctrl+C) AFTER PREPARE but BEFORE decision
**Step 3:** Participants are stuck in READY state (BLOCKING)

**Manual steps:**
1. Modify coordinator to add a sleep before sending decision:
   ```python
   # After "GLOBAL-COMMIT" log
   time.sleep(30)  # Pause here
   ```
2. Start transaction
3. Kill coordinator during the sleep
4. Check participants - they're blocked!



---

### Test 4: Successful 3PC Transaction

**Restart coordinator with 3PC:**
```bash
python3 coordinator_server.py --id COORD --port 8000 \
  --participants B:184.73.13.182:8001,C:100.48.82.58:8002 \
  --protocol 3PC
```

**Trigger 3PC transaction:**
```bash
python3 client_http.py --coordinator localhost:8000 --tx TX003 --op "x=-10" --protocol 3PC
```

**Expected output:**
```
[Coordinator] TX003 INIT
[Coordinator] TX003 CAN-COMMIT
[Coordinator] TX003 PRE-COMMIT
[Coordinator] TX003 DO-COMMIT
[Coordinator] TX003 COMMITTED (3PC)
```



---

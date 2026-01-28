# Distributed Transactions Lab - 2PC & 3PC

## Lab Information
- **Nodes**: 3 EC2 instances (1 coordinator + 2 participants)
- **Protocols**: Two-Phase Commit (2PC) and Three-Phase Commit (3PC)
- **Key Pair**: transaction
- **Security Group**: Ports 8000-8010 (TCP), Port 22 (SSH)

## Your EC2 Instances
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

### Test 1: Successful 2PC Transaction (Screenshot #1)

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

**📸 TAKE SCREENSHOT #1** - Shows successful 2PC

---

### Test 2: Failed Transaction - Participant Timeout (Screenshot #2)

**Stop Participant C (Ctrl+C in Terminal 3)**

**Trigger transaction:**
```bash
python3 client_http.py --coordinator localhost:8000 --tx TX002 --op "x=-10" --protocol 2PC
```

**Expected:**
- Coordinator times out waiting for Participant C
- Transaction ABORTS

**📸 TAKE SCREENSHOT #2** - Shows timeout and abort

**Restart Participant C after test**

---

### Test 3: Coordinator Crash - Blocking (Screenshot #3)

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

**📸 TAKE SCREENSHOT #3** - Participants stuck in READY state

---

### Test 4: Successful 3PC Transaction (Screenshot #4)

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

**📸 TAKE SCREENSHOT #4** - Shows 3PC three phases

---

### Test 5: 3PC Non-Blocking (Screenshot #5)

**Key difference:** In 3PC, if coordinator fails after PRE-COMMIT, participants can complete the transaction.

This is THEORETICAL in our implementation, but you can explain it in your report.

**📸 TAKE SCREENSHOT #5** - AWS Console showing 3 running instances

---

## SCREENSHOTS FOR REPORT

1. **Screenshot #1**: Successful 2PC transaction with all phases
2. **Screenshot #2**: Failed transaction due to participant timeout
3. **Screenshot #3**: Blocking behavior when coordinator crashes
4. **Screenshot #4**: Successful 3PC showing all three phases
5. **Screenshot #5**: AWS EC2 console showing 3 running instances
6. **Screenshot #6**: Security group inbound rules

---

## DELIVERABLES CHECKLIST

### ✅ Code Repository
- [x] coordinator_server.py
- [x] participant.py
- [x] client_http.py
- [x] README.md (this file)

### ✅ Report Sections
1. **Introduction** - Brief overview of 2PC and 3PC
2. **System Architecture** - Diagram of your 3 nodes
3. **2PC Implementation** - Screenshots of successful & failed transactions
4. **Failure Scenarios** - Blocking demonstration
5. **3PC Implementation** - Screenshots of 3-phase execution
6. **Comparison** - 2PC vs 3PC table
7. **Conclusion** - What you learned

---

## TROUBLESHOOTING

**Problem: Cannot connect to participant**
- Check security group allows ports 8000-8010
- Verify participant is running: `ps aux | grep participant`
- Check firewall: `sudo ufw status`

**Problem: Connection timeout**
- Use PUBLIC IPs in coordinator participants list
- Verify all instances are in same region/VPC
- Test connectivity: `telnet <ip> <port>`

**Problem: Module not found**
- Install dependencies: `pip3 install flask requests`
- Use python3 (not python)

---

## CLEANUP

After completing the lab:
```bash
# Stop all processes
pkill -f python3

# Remove files (optional)
rm -rf ~/distributed-tx
```

---

## EVALUATION RUBRIC MAPPING

| Criterion | Points | How to Score |
|-----------|--------|--------------|
| Correct 2PC implementation | 30 | Tests 1-2 working |
| Failure scenario demonstrated | 20 | Test 3 (blocking) |
| Clear logs and states | 10 | Screenshots show logs |
| Correct 3PC implementation | 30 | Test 4 working |
| Explanation of limitations | 10 | Report comparison section |

**Total: 100 points**

---

## QUICK REFERENCE COMMANDS

```bash
# Start Participant
python3 participant.py --id <ID> --port <PORT>

# Start Coordinator (2PC)
python3 coordinator_server.py --id COORD --port 8000 \
  --participants B:IP:8001,C:IP:8002 --protocol 2PC

# Start Coordinator (3PC)
python3 coordinator_server.py --id COORD --port 8000 \
  --participants B:IP:8001,C:IP:8002 --protocol 3PC

# Trigger Transaction
python3 client_http.py --coordinator localhost:8000 \
  --tx TX001 --op "x=-10" --protocol 2PC

# Check if process is running
ps aux | grep python3

# Kill all Python processes
pkill -f python3
```

---

## PROTOCOL COMPARISON

| Feature | 2PC | 3PC |
|---------|-----|-----|
| Phases | 2 | 3 |
| Blocking | Yes (coordinator crash) | Reduced |
| Messages | 3n | 5n |
| Complexity | Lower | Higher |
| Fault Tolerance | Lower | Higher |

---

Good luck with your lab! 🚀

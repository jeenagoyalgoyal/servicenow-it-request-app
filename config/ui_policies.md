# UI Policies

## 1. Require justification for high-cost requests
- **Table:** IT Service Request
- **Conditions:** Estimated cost **greater than** 1000
- **On load:** true · **Reverse if false:** true
- **Action:** Justification → Visible: true, Mandatory: true

## 2. Lock priority
- **Table:** IT Service Request
- **Conditions:** none (always)
- **Action:** Priority → Read only: true

## 3. Lock closed requests
- **Table:** IT Service Request
- **Conditions:** State **is one of** Closed Complete, Closed Incomplete
- **Actions:** Category, Estimated cost, Justification, Impact, Urgency → Read only: true

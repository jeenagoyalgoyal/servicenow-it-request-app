# ATF Form Tests

Create these in **Automated Test Framework > Tests**. Each test starts with **Impersonate** (for example *Abel Tuter*) and ends by checking the saved record.

## Test 1: Auto priority and routing
1. Open a New Form: IT Service Request
2. Set Field Values: Category = Hardware, Impact = 1 - High, Urgency = 1 - High, Short description = "Laptop not booting"
3. Submit a Form
4. Record Validation: Priority = 1 - Critical, Assignment group = Hardware

## Test 2: Duplicate request blocked
1. Record Insert: IT Service Request, Requested for = Abel Tuter, Category = Software, State = New
2. Open a New Form: IT Service Request
3. Set Field Values: Requested for = Abel Tuter, Category = Software
4. Submit a Form (**Assert type:** form submission cancelled in browser / record not inserted)

## Test 3: Justification required over $1,000
1. Open a New Form: IT Service Request
2. Set Field Values: Category = Hardware, Estimated cost = 1500
3. UI Policy check: Justification is **mandatory**
4. Submit a Form (expect failure)
5. Set Field Values: Justification = "Replacement for failed laptop"
6. Submit a Form (expect success)

## Test 4: REST API returns JSON
1. Record Insert: an IT Service Request
2. Send REST Request – Inbound: GET `/api/x_<scope>/it_service_requests/request/{number}`
3. Assert Status Code = 200; Assert JSON Response Payload Element `result.number` = inserted number

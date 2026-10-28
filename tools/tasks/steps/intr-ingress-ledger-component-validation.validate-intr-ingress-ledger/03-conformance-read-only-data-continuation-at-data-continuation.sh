python3 org-runtime/intr_protocol.py conform --org "Data-Continuation" > conform.json
python3 -c 'import json; r=json.load(open("conform.json")); assert r["disposition"]=="ALLOW", r; print("INTR_DESTINATION_CONFORMS", r["disposition"])'

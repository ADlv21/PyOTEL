import json

data = "{\"messages\": [{\"message\": \"Started\", \"type\": \"log\", \"timestamp\": \"2025-04-30T16:11:05.431482\"}, {\"message\": \"Finished\", \"type\": \"log\", \"timestamp\": \"2025-04-30T16:11:05.431587\"}, {\"message\": \"Inside root endpoint\", \"type\": \"print\", \"timestamp\": \"2025-04-30T16:11:05.431614\"}], \"trace_id\": \"66f60f06-7487-453a-849e-db0107416b4b\", \"type\": \"batch\", \"timestamp\": \"2025-04-30T16:11:05.913616\"}"

print(type(data))
print(data)

data = json.loads(data)
print(type(data))
print(data)
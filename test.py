import json

data = "{\"trace_id\": \"e33e6370-401e-4550-ab7e-8bc3817003d4\", \"method\": \"GET\", \"path\": \"/\", \"query_params\": {}, \"status_code\": 200, \"duration_ms\": 2.18, \"ip\": \"127.0.0.1\", \"user_agent\": \"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36\", \"headers\": {\"host\": \"127.0.0.1:8000\", \"connection\": \"keep-alive\", \"cache-control\": \"max-age=0\", \"sec-ch-ua\": \"\\\"Google Chrome\\\";v=\\\"135\\\", \\\"Not-A.Brand\\\";v=\\\"8\\\", \\\"Chromium\\\";v=\\\"135\\\"\", \"sec-ch-ua-mobile\": \"?0\", \"sec-ch-ua-platform\": \"\\\"macOS\\\"\", \"upgrade-insecure-requests\": \"1\", \"user-agent\": \"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36\", \"accept\": \"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7\", \"sec-fetch-site\": \"none\", \"sec-fetch-mode\": \"navigate\", \"sec-fetch-user\": \"?1\", \"sec-fetch-dest\": \"document\", \"accept-encoding\": \"gzip, deflate, br, zstd\", \"accept-language\": \"en-GB,en-US;q=0.9,en;q=0.8\", \"dnt\": \"1\", \"sec-gpc\": \"1\"}, \"cookies\": {}}"

print(type(data))
print(data)

data = json.loads(data)
print(type(data))
print(data)
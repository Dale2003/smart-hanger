import json
with open(r"/home/ubuntu/tcp_test/result.json", 'r', encoding='utf-8') as f:
    result = json.load(f)
is_dry = result["dry"]
is_dangerous = result["dangerous_weather"]
print(f"是否干燥：{'是'if is_dry == 'True' else '否'}，\n是否有危险天气：{'是'if is_dangerous == 'True' else '否'}")
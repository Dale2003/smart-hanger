import json

with open(r"/home/ubuntu/tcp_test/data.json", 'r', encoding='utf-8') as f:
    data = f.readlines()

# 解析最后一行的 JSON 数据
if data:
    # 把data按照时间排序
    data.sort(key=lambda x: json.loads(x)["time"], reverse=True)
    last_entry = json.loads(data[1])
    temperature_info = last_entry["data"]
    temperature_value = temperature_info.split(":")[2].split("C")[0]
    hum_value = temperature_info.split(":")[1].split("%")[0]
    time_info = last_entry["time"]
    weight_value = temperature_info.split(":")[3].split("\n")[0]
    weight_value = int(weight_value)
    weight_value /= 1000
    if weight_value >= 8242:
        weight_value = 0
    else:
        weight_value_temp = 8242 - weight_value
        weight_value = weight_value_temp
    weight_value /= 0.97
    print(f"最后一次采样时间：{time_info}，温度：{temperature_value}度，湿度：{hum_value}%，重量：{weight_value:.2f}g")
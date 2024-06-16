import requests
from bs4 import BeautifulSoup
import json

def getHTMLtext(url):
    """Request and retrieve the HTML content of a webpage."""
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        print("Successfully accessed the URL")
        return r.text
    except requests.RequestException as e:
        print(f"Error accessing the URL: {e}")
        return ""

def get_content(html):
    """Process and extract useful information from HTML content."""
    final = []  # Initialize a list to store 7-day forecast data
    bs = BeautifulSoup(html, "html.parser")  # Create a BeautifulSoup object
    body = bs.body
    data = body.find('div', {'id': '7d'})  # Find the div with id='7d' for 7-day forecast
    
    # Extract today's weather data
    data2 = body.find_all('div', {'class': 'left-div'})
    script_text = data2[2].find('script').string
    json_text = script_text[script_text.index('=') + 1:-2]  # Convert JavaScript to JSON
    jd = json.loads(json_text)
    dayone = jd['od']['od2']  # Extract today's data
    final_day = []  # Store today's data
    for count, entry in enumerate(dayone):
        if count <= 23:
            temp = [
                entry['od21'],  # Time
                entry['od22'],  # Temperature
                entry['od24'],  # Wind direction
                entry['od25'],  # Wind scale
                entry['od26'],  # Precipitation
                entry['od27'],  # Humidity
                entry['od28']   # Air quality
            ]
            final_day.append(temp)
    
    # Reverse the order of the final_day list to ensure chronological order
    final_day.reverse()
    
    # Extract 7-day weather data
    ul = data.find('ul')  # Find all ul tags
    li = ul.find_all('li')  # Find all li tags
    for i, day in enumerate(li):
        if 0 < i < 7:  # Skip the first and limit to next 6 days
            temp = []  # Temporary list for each day's data
            date = day.find('h1').string  # Get date
            temp.append(date[:date.index('日')])
            inf = day.find_all('p')  # Find all p tags within li
            
            temp.append(inf[0].string)  # Weather description
            
            low_temp = inf[1].find('i').string  # Low temperature
            temp.append(low_temp[:-1])
            
            high_temp_tag = inf[1].find('span')  # High temperature
            if high_temp_tag:
                temp.append(high_temp_tag.string[:-1])
            else:
                temp.append(None)
            
            wind = inf[2].find_all('span')  # Wind direction
            for j in wind:
                temp.append(j['title'])
            
            wind_scale = inf[2].find('i').string  # Wind scale
            temp.append(int(wind_scale[wind_scale.index('级') - 1]))
            
            final.append(temp)
    
    return final_day, final

def write_to_json(file_name, data, day=14):
    """Save weather data to a JSON file."""
    with open(file_name, 'w', encoding='utf-8') as f:
        if day == 14:
            keys = ['date', 'weather', 'low_temperature', 'high_temperature', 'wind_direction1', 'wind_direction2', 'wind_scale']
        else:
            keys = ['hour', 'temperature', 'wind_direction', 'wind_scale', 'precipitation', 'humidity', 'air_quality']
        json_data = [dict(zip(keys, d)) for d in data]
        json.dump(json_data, f, ensure_ascii=False, indent=4)

def main1():
    """Main function to execute the weather data extraction and saving."""
    print("Weather Data Extraction")
    url1 = 'http://www.weather.com.cn/weather/101010200.shtml'  # URL for 7-day weather forecast
    
    html1 = getHTMLtext(url1)
    if html1:
        data1, data1_7 = get_content(html1)  # Get today's and 7-day forecast data
        
        # Save data to JSON files
        write_to_json('weather1.json', data1, 1)
        write_to_json('weather14.json', data1_7, 14)


import json
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
import time as t  # 将 time 模块重命名为 t

# 读取JSON文件
def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# 解析data.json文件
def parse_data_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    records = []
    for line in lines:
        if "humi" in line and "temp" in line and "weight" in line:
            record = {}
            time_str, data_str = line.strip().split('", "data": "')
            time_str = time_str.replace('{"time": "', '')
            data_str = data_str.replace('"}', '')
            record['time'] = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            data_parts = data_str.split(',')
            for part in data_parts:
                key, value = part.split(':')
                if key.strip() == "weight":
                    # 忽略weight的后三位，并转换单位
                    record[key.strip()] = int(value.strip().replace("\\n", "")) // 1000 * 50 / 40000
                else:
                    record[key.strip()] = float(value.strip('%Ckg'))
            records.append(record)
    return records

# 将数据按分钟聚合
def aggregate_by_minute(data_records):
    aggregated_data = {}
    for record in data_records:
        minute = record['time'].replace(second=0)
        if minute not in aggregated_data:
            aggregated_data[minute] = {'humi': [], 'weight': []}
        aggregated_data[minute]['humi'].append(record['humi'])
        aggregated_data[minute]['weight'].append(record['weight'])

    aggregated_records = []
    for minute, values in aggregated_data.items():
        avg_humi = np.mean(values['humi'])
        avg_weight = np.mean(values['weight'])
        aggregated_records.append({'time': minute, 'humi': avg_humi, 'weight': avg_weight})

    aggregated_records.sort(key=lambda x: x['time'])
    return aggregated_records

# 线性回归法判断衣物是否晾干
def is_clothes_dry_trend_analysis(data_records, long_window_minutes=60, short_window_minutes=10):
    if len(data_records) < 2:
        return False
    
    # 获取最近long_window_minutes和short_window_minutes内的记录
    end_time = data_records[-1]['time']
    long_start_time = end_time - timedelta(minutes=long_window_minutes)
    short_start_time = end_time - timedelta(minutes=short_window_minutes)
    
    long_window_records = [record for record in data_records if record['time'] >= long_start_time]
    short_window_records = [record for record in data_records if record['time'] >= short_start_time]
    
    if len(long_window_records) < 2 or len(short_window_records) < 2:
        return False
    
    # 提取时间、湿度和重量
    long_times = [(record['time'] - long_window_records[0]['time']).total_seconds() / 60 for record in long_window_records]
    long_humidities = [record['humi'] for record in long_window_records]
    long_weights = [record['weight'] for record in long_window_records]
    
    short_times = [(record['time'] - short_window_records[0]['time']).total_seconds() / 60 for record in short_window_records]
    short_humidities = [record['humi'] for record in short_window_records]
    short_weights = [record['weight'] for record in short_window_records]
    
    # 线性回归分析湿度和重量随时间的变化趋势
    long_times = np.array(long_times).reshape(-1, 1)
    short_times = np.array(short_times).reshape(-1, 1)
    
    long_humidity_model = LinearRegression().fit(long_times, long_humidities)
    long_weight_model = LinearRegression().fit(long_times, long_weights)
    
    short_humidity_model = LinearRegression().fit(short_times, short_humidities)
    short_weight_model = LinearRegression().fit(short_times, short_weights)
    
    long_humidity_slope = long_humidity_model.coef_[0]
    long_weight_slope = long_weight_model.coef_[0]
    
    short_humidity_slope = short_humidity_model.coef_[0]
    short_weight_slope = short_weight_model.coef_[0]
    
    # 打印斜率以便调试
    # print(f"Long window humidity slope: {long_humidity_slope}")
    # print(f"Long window weight slope: {long_weight_slope}")
    # print(f"Short window humidity slope: {short_humidity_slope}")
    # print(f"Short window weight slope: {short_weight_slope}")
    
    # 判断湿度和重量的变化率是否显著减小
    if np.abs(short_humidity_slope) <= np.abs(long_humidity_slope) and np.abs(short_weight_slope) < np.abs(long_weight_slope):
        return True
    return False

# 判断未来天气是否对晾衣物有危险
def is_weather_dangerous(weather1, weather14):
    # 未来24小时的天气预报

    # for forecast in weather1:
    #     if float(forecast['precipitation']) > 0 or int(forecast['wind_scale']) >= 5:
    #         return True


    # 未来7天的天气预报
    for forecast in weather14:
        if '雨' in forecast['weather'] or forecast['wind_scale'] >= 5:
            return True
        break

    return False

# 主函数
def main2():
    while True:
        weather1 = read_json('weather1.json')
        weather14 = read_json('weather14.json')
        data_records = parse_data_json('data.json')
        aggregated_records = aggregate_by_minute(data_records)

        dry = is_clothes_dry_trend_analysis(aggregated_records, long_window_minutes=2, short_window_minutes=1)
        weather_dangerous = is_weather_dangerous(weather1, weather14)

        if dry:
            print("衣物已经晾干。")
        else:
            print("衣物尚未晾干。")

        if weather_dangerous:
            print("未来的天气对衣物晾晒有危险，请注意。")
        else:
            print("未来的天气适合晾晒衣物。")

        result = {"dry": str(dry), "dangerous_weather": str(weather_dangerous)}
        with open('result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        # break
        t.sleep(120)  # 600秒 = 10分钟


# main()

main1()
main2()
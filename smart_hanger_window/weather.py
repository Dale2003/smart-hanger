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
import re
import pandas as pd
import time as t  # 将 time 模块重命名为 t

def is_dry_trend(df_resampled):
    # 计算最近几个小时内的湿度和重量变化
    recent_hours = 5  # 选择检查最近5个小时的趋势
    # if len(df_resampled) < recent_hours:
    #     return False  # 数据不足以判断
    
    humidity_trend = df_resampled['humidity'].diff().tail(recent_hours).mean()
    weight_trend = df_resampled['weight'].diff().tail(recent_hours).mean()

    print(humidity_trend)
    # 判断规则：湿度变化小且重量变化小
    humidity_stable = abs(humidity_trend) < 1  # 湿度变化在1%以内
    weight_stable = abs(weight_trend) < 10000  # 重量变化小于10000

    return humidity_stable and weight_stable

def is_weather_dangerous(weather1, weather14):
    # 检查未来24小时天气
    for hour_data in weather1:
        if float(hour_data['precipitation']) > 0 or int(hour_data['wind_scale']) >= 5:
            return True
    
    # 检查未来7天天气
    for day_data in weather14:
        if '雨' in day_data['weather'] or int(day_data['wind_scale']) >= 5:
            return True
    
    return False

def main2():
    while True:

        # 读取并解析 weather1.json
        with open('weather1.json', 'r', encoding='utf-8') as f:
            weather1 = json.load(f)

        # 读取并解析 weather14.json
        with open('weather14.json', 'r', encoding='utf-8') as f:
            weather14 = json.load(f)

        # 读取并解析 data.json
        with open('data.json', 'r', encoding='utf-8') as f:
            data_lines = f.readlines()
            data = []
            for line in data_lines:
                try:
                    entry = json.loads(line)
                    if re.match(r"humi:\d+%,temp:\d+\.\d+C,weight:\d+", entry['data']):
                        data.append(entry)
                except json.JSONDecodeError:
                    continue

        # 提取有效数据
        parsed_data = []
        for entry in data:
            time = entry['time']
            data_split = entry['data'].split(',')
            humidity = int(data_split[0].split(':')[1].replace('%', ''))
            temperature = float(data_split[1].split(':')[1].replace('C', ''))
            weight = int(data_split[2].split(':')[1])
            weight = weight // 1000  # 忽略后三位
            parsed_data.append([time, humidity, temperature, weight])

        df = pd.DataFrame(parsed_data, columns=['time', 'humidity', 'temperature', 'weight'])

        # 将时间列转换为 datetime 类型
        df['time'] = pd.to_datetime(df['time'])

        # 按时间排序
        df = df.sort_values('time')

        # 计算每小时的平均值
        df.set_index('time', inplace=True)
        # df_resampled = df.resample('H').mean().dropna().reset_index()
        df_resampled = df.resample('10T').mean().dropna().reset_index()

        print(df_resampled)
        dry = is_dry_trend(df_resampled)
        # print(f"衣物是否晾干: {'是' if dry else '否'}")
        print(dry)


        dangerous = is_weather_dangerous(weather1, weather14)
        # print(f"天气是否对衣物有危险: {'是' if dangerous else '否'}")

        result = {"dry": str(dry), "dangerous_weather": str(dangerous)}
        with open('result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        # break
        t.sleep(600)  # 600秒 = 10分钟
main1()
main2()
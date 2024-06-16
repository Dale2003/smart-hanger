import threading
import socket
import json
import time

encoding = 'utf-8'
BUFSIZE = 1024

##读取端口消息
class Reader(threading.Thread):
    def __init__(self, client):##获取客户端
        threading.Thread.__init__(self)
        self.client = client

    def run(self):##持续接收消息并处理
        with open(r"/home/ubuntu/tcp_test/data.json", "w") as f:
            pass
        while True:
            data = self.client.recv(BUFSIZE)##接收字节消息
            if data:
                try:
                    string = data.decode(encoding)##转化为字符串
                    print(string)##打印接收到的消息
                    # 把接收到的消息中的数字和当前时间一起存成json文件，一共只保留1000条数据
                    current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                    data_json = {"time": current_time, "data": string} 
                    with open("/home/ubuntu/tcp_test/data.json", "a") as f:
                        json.dump(data_json, f)
                        f.write("\n")
                    with open(r"/home/ubuntu/tcp_test/data.json", 'r', encoding='utf-8') as f:
                        data = f.readlines()
                    if len(data) > 1000:
                        with open("/home/ubuntu/tcp_test/data.json", "w") as f:
                            # 按时间排序，只保留最近的1000条数据
                            data.sort(key=lambda x: json.loads(x)["time"], reverse=True)
                            for i in range(1000):
                                f.write(data[i])
                except:
                    print("Error")
            else:
                break

##建立端口监听
class Listener(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", port))
        self.sock.listen(0)

    def run(self):
        # 清空json文件
        print("listener started")
        while True:
            client, cltadd = self.sock.accept()
            Reader(client).start()

lst = Listener(1234)  # create a listen thread
lst.start()  # then start

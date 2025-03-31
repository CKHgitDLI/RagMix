import json
import requests
import time
import random


def sse_ask(task):
    url = "http://59.74.169.90:8080/chat"  # API地址
    random_num1 = random.randint(1, 190129)
    random_num2 = random.randint(1345, 3454555)
    data = {
        "ask": f"现在工作面最大值为Emax={random_num1}J，总能量：∑E={random_num2}J/每5m推进度,是什么危险状态？"}  # 用户问题
    print(data)
    headers = {
        'Accept': 'text/event-stream',
        'Content-Type': 'application/json'
    }
    json_data = json.dumps(data)
    response = requests.post(url, data=json_data, headers=headers, stream=True)
    if response.status_code == 200:
        buffer = ''
        for line in response.iter_lines(decode_unicode=False):
            line = line.decode('utf-8')
            if line.startswith('data:'):
                data = line[5:].strip()
                if data == '[DONE]':
                    break
                buffer += data
                # current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                # str_t=current_time+":任务"+str(task)+":"
                # print("\033[31m",str_t,"\033[0m",len(json.loads(buffer)['content']))
                update_process(task, len(json.loads(buffer)['content']))
            elif line.strip() == '':
                if buffer:
                    buffer = ''
        update_process(task, "done")
    else:
        raise Exception(f"请求失败，状态码：{response.status_code}")


dict = {}


def update_process(task, len):
    global dict
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    if len == "done":
        dict["任务" + str(task)] = current_time + "完成"
    else:
        dict["任务" + str(task)] = dict.get("任务" + str(task), 0) + 1
    text_to_append = '\n' + current_time + ":" + str(dict)
    with open('log30-32b.txt', 'a', encoding='utf-8') as file:  # 日志保存到txt
        file.write(text_to_append)
    print(current_time + ":" + str(dict))


import threading


def main():
    vu_num = 30  # 并发用户数量
    threads = []
    for i in range(vu_num):
        t = threading.Thread(target=sse_ask, kwargs={"task": i})
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()

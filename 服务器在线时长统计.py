# -*- coding: utf-8 -*-
'''
@Author  : Hatanezumi
@Contact : Hatanezumi@chunshengserver.cn
'''
import sys
import gzip
import datetime
import traceback
from pathlib import Path

version = '1.0.0'
LOGINMESSAGE = r'logged in with entity id'
LOGOUTMESSAGE = r'lost connection'

def get_time(text: str) -> str|None:
    '''
    返回行信息的时间
    '''
    if not text.startswith('['):
        return None
    text_temp = text.removeprefix('[')
    time = text_temp.split(']',1)[0]
    return time

def get_player_id(text: str) -> str|None:
    '''
    返回行中的玩家id
    仅登录和登出信息
    '''
    if not text.startswith('['):
        return None
    text_temp = text.split(':',3)
    if len(text_temp) == 3:
        return None
    text_temp = text_temp[3].lstrip()
    if LOGINMESSAGE in text_temp:
        return text_temp.split('[')[0]
    elif LOGOUTMESSAGE in text_temp:
        return text_temp.split(' ',1)[0]
    else:
        return None

def analyze(log_path: Path) -> dict[str, list[list[str, str]]]:
    '''
    分析玩家的在线时间
    返回字典Key:玩家id value:玩家的上线及下线的时间点
    '''
    try:
        with open(log_path, 'r',encoding='utf-8') as file:
            data = file.readlines()
    except:
        try:
            with open(log_path, 'r',encoding='gbk') as file:
                data = file.readlines()
        except:
            print(f'文件打开失败:{traceback.format_exc()}')
            return {}
    res = {}
    l_time = '00:00:00'
    for line in data:
        time = get_time(line)
        if time:
            l_time = time
        if LOGINMESSAGE in line:
            id = get_player_id(line)
            if id.startswith('com'):
                continue
            if '.' in id:
                continue
            if time is None or id is None:
                continue
            if id not in res.keys():
                res[id] = [[time]]
                continue
            res[id].append([time])
        elif LOGOUTMESSAGE in line:
            id = get_player_id (line)
            if id.startswith('com'):
                continue
            if '.' in id:
                continue
            if time is None or id is None:
                continue
            if id not in res.keys():
                res[id] = [[None,time]]
                continue
            if len(res[id][-1]) == 2:
                res[id][-1][-1] = time
            else:
                res[id][-1].append(time)
    for id in res.keys():
        if len(res[id][-1]) == 1:
            res[id][-1].append(l_time)
    return res

def count_data(data: dict[str, list[list[str, str]]]) -> dict[str, float]:
    '''
    返回玩家的在线时间(单位秒)
    '''
    res = {}
    for id in data.keys():
        for start_time, end_time in data[id]:
            this_time = datetime.datetime.strptime(end_time,'%H:%M:%S') - datetime.datetime.strptime(start_time,'%H:%M:%S') if start_time is not None else datetime.datetime.strptime(end_time,'%H:%M:%S') - datetime.datetime.strptime('00:00:00','%H:%M:%S')
            res[id] = this_time.total_seconds() + float(res[id]) if id in res.keys() else this_time.total_seconds()
    return res

def count(data1: dict[str, float], data2: dict[str, float]) -> dict[str, float]:
    '''
    对已经处理好的数据相加
    '''
    res = data1.copy()
    for id in data2.keys():
        res[id] = res[id] + data2[id] if id in res.keys() else data2[id]
    return res

def get_max_player(data: dict[str, float]) -> tuple[str, float]:
    '''
    返回时间最长的玩家
    '''
    max_id = None
    max_time = 0
    for id in data.keys():
        if max_time < data[id]:
            max_id = id
            max_time = data[id]
    return (max_id, max_time)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('请在后面接log文件或log文件夹')
        sys.exit(0)
    temp_dir = Path('temp')
    if not temp_dir.exists():
        temp_dir.mkdir()
    res_data = {}
    for i, arg in enumerate(sys.argv):
        if i == 0:
            continue
        log_path = Path(arg)
        if log_path.is_dir():
            for log_file in log_path.iterdir():
                if log_file.name.endswith('.gz'):
                    print(f'\r分析:{log_file}',end='')
                    temp_log = temp_dir / 'temp.log'
                    try:
                        with open(log_file, 'rb') as file:
                            data = gzip.decompress(file.read())
                    except:
                        print(f'{traceback.format_exc()}')
                        continue
                    try:
                        data = data.decode('gbk')
                    except:
                        try:
                            data = data.decode('utf-8')
                        except:
                            print(f'{traceback.format_exc()}')
                            continue
                    with open(temp_log,'w',encoding='utf-8') as file:
                        file.write(data)
                    res_data = count(res_data,count_data(analyze(temp_log)))
                elif log_file.name.endswith('.log'):
                    print(f'\r分析:{log_file}',end='')
                    res_data = count(res_data,count_data(analyze(log_file)))
        else:
            print(f'\r分析:{log_path}',end='')
            res_data = count(res_data,count_data(analyze(log_path)))
    print('\n分析完成,结果保存在res.txt')
    print(f'玩家数:{len(res_data.keys())}')
    max_id, max_time = get_max_player(res_data)
    print(f'在线时长最长玩家:{max_id},时长:{max_time}秒')
    res_text = '玩家id:在线时长(秒)\n'
    for player_id in res_data.keys():
        res_text += f'{player_id}:{res_data[player_id]}\n'
    res_text.removesuffix('\n')
    with open(Path('res.txt'),'w',encoding='utf-8') as file:
        file.write(str(res_text))
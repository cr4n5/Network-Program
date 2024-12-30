import socket
import threading
import os
import json


# 初始化用户信息
def init_users():
    global users, online_users

    if os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            users = json.load(f)
    else:
        users = {}

    if os.path.exists('online_users.json'):
        with open('online_users.json', 'r') as f:
            online_users = json.load(f)
    else:
        online_users = {}

def handle_client(data, addr, server_socket):
    message = data.decode('utf-8')
    command, *params = message.split(' ')

    if command == 'PING': # 心跳检测
        server_socket.sendto("PONG".encode('utf-8'), addr)

    elif command == 'REGISTER': # 注册
        username, password = params
        if username in users:
            server_socket.sendto("用户名已存在".encode('utf-8'), addr)
        else:
            users[username] = password
            server_socket.sendto("注册成功".encode('utf-8'), addr)
            with open('users.json', 'w') as f:
                json.dump(users, f, indent=4)

    elif command == 'LOGIN': # 登录
        username, password = params
        if username in users and users[username] == password:
            online_users[username] = addr
            server_socket.sendto("登录成功".encode('utf-8'), addr)
            with open('online_users.json', 'w') as f:
                json.dump(online_users, f, indent=4)
        else:
            server_socket.sendto("用户名或密码错误".encode('utf-8'), addr)

    elif command == 'PUBLIC': # 公共消息
        username, msg = params[0], ' '.join(params[1:])
        for user, address in online_users.items():
            if user != username:
                print(f"{username}: {msg}")
                print(address)
                server_socket.sendto(f"{username}: {msg}".encode('utf-8'), tuple(address))

    elif command == 'PRIVATE': # 私聊
        sender, receiver, msg = params[0], params[1], ' '.join(params[2:])
        if receiver in online_users:
            print(f"{sender} (私聊): {msg}")
            print(online_users[receiver])
            server_socket.sendto(f"{sender} (私聊): {msg}".encode('utf-8'), tuple(online_users[receiver]))
        else:
            server_socket.sendto("用户不在线".encode('utf-8'), addr)

    elif command == 'EXIT': # 退出
        username = params[0]
        if username in online_users:
            del online_users[username]
            server_socket.sendto("退出成功".encode('utf-8'), addr)
            with open('online_users.json', 'w') as f:
                json.dump(online_users, f, indent=4)
        else:
            server_socket.sendto("用户不在线".encode('utf-8'), addr)
    
    elif command == "GET_ALL_USERS_STATUS": # 所有用户在线状态
        data = {}
        for user, password in users.items():
            if user in online_users:
                data[user] = "True"
            else:
                data[user] = "False"
        server_socket.sendto(json.dumps(data).encode('utf-8'), addr)


def main():
    # 初始化用户信息
    init_users()

    # 创建 UDP 套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', 12345))

    print("服务器已启动...")

    while True:
        try:
            data, addr = server_socket.recvfrom(1024)
            print(f"收到来自 {addr} 的消息: {data.decode('utf-8')}")
            threading.Thread(target=handle_client, args=(data, addr, server_socket)).start()
        except OSError as e:
            print(f"处理客户端请求时出错: {e}")

if __name__ == "__main__":
    main()
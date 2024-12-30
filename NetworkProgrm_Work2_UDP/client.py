import socket
import threading
import flet as ft
import sys
import time

# 客户端套接字
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('127.0.0.1', 12345)
client_socket.connect(server_address)

# 检查服务器是否在线
def check_server_online(get_data=1):
    if get_data == 1:
        try:
            client_socket.settimeout(2)
            client_socket.sendto("PING".encode('utf-8'), server_address)
            data, _ = client_socket.recvfrom(1024)
            if data.decode('utf-8') == "PONG":
                return True
        except socket.timeout:
            client_socket.settimeout(None)
            return False
        except Exception as e:
            print(f"检查服务器在线时出错: {e}")
        client_socket.settimeout(None)
        return False
    else:
        try:
            print("检查服务器是否在线")
            client_socket.settimeout(2)
            client_socket.sendto("PING".encode('utf-8'), server_address)
        except Exception as e:
            print(f"检查服务器在线时出错: {e}")

# 获取全部用户列表及在线状态
def receive_all_users(get_data=1):
    # 若get_data为1，则返回在线用户列表，否则更新page
    if get_data == 1:
        try:
            client_socket.sendto("GET_ALL_USERS_STATUS".encode('utf-8'), server_address)
            data, _ = client_socket.recvfrom(1024)
            data = data.decode('utf-8')
            # 转化为列表
            online_users = eval(data)
            print(f"获取用户: {online_users}")
            return online_users
        except OSError as e:
            print(f"获取用户时出错: {e}")
            return None
    else:
        try:
            client_socket.sendto("GET_ALL_USERS_STATUS".encode('utf-8'), server_address)
        except OSError as e:
            print(f"获取用户时出错: {e}")

# 处理消息
def handle_message(page, public_chat_display, private_chat_displays, message):
    global username, private_chat_tab, private_chat_tabs
     # 如果为PING或PONG
    if message == "PONG":
        server_status.style = ft.TextStyle(color="green")
        client_socket.settimeout(None)
        page.update()
    # 如果为用户列表
    elif message[0]=="{":
        print(f"用户列表: {message}")
        all_users = eval(message)
        # 更新私聊选项卡
        for user, status in all_users.items():
            if user != username and status=='True':
                if user not in private_chat_displays:
                    private_chat_displays[user] = ft.Column()
                    private_chat_tabs.append(ft.Tab(text=user, content=private_chat_displays[user], icon=ft.Icon(name="check_circle")))
                else:
                    for tab in private_chat_tabs:
                        if tab.text == user:
                            tab.icon = ft.Icon(name="check_circle")
            elif user != username and status=='False':
                if user not in private_chat_displays:
                    private_chat_displays[user] = ft.Column()
                    private_chat_tabs.append(ft.Tab(text=user, content=private_chat_displays[user], icon=ft.Icon(name="error")))
                else:
                    for tab in private_chat_tabs:
                        if tab.text == user:
                            tab.icon = ft.Icon(name="error")
        # 设置ft.Tabs(tabs=private_chat_tabs)
        private_chat_tab.content.controls[3].tabs = private_chat_tabs
        page.update()
    # 如果为公共消息或私聊消息
    elif ":" in message:
        if "私聊" in message:# 私聊消息
            # 私聊消息
            sender, msg = message.split(":", 1)
            receiver = sender.split()[0]
            try:
                private_chat_displays[receiver].controls.append(ft.Text(message))
            except Exception as e:
                print(f"接收私聊消息时出错: {e}")
                threading.Thread(target=receive_all_users, args=(0,)).start()
                time.sleep(1)
                private_chat_displays[receiver].controls.append(ft.Text(message))
            page.update()
        else:
            # 公共消息
            public_chat_display.controls.append(ft.Text(message))
            page.update()
    elif message == "退出成功":
        show_info_dialog(page,"退出成功")
        # 关闭程序
        page.controls.clear()
        page.update()
        sys.exit()
    else:
        show_error_dialog(page, message)


# 接收消息
def receive_messages(page, public_chat_display, private_chat_displays):
    global username, private_chat_tab, private_chat_tabs
    while True:
        try:
            data, _ = client_socket.recvfrom(1024)  # f"{sender} (私聊): {msg}"
            message = data.decode('utf-8')
            print(f"收到消息: {message}")
            threading.Thread(target=handle_message, args=(page, public_chat_display, private_chat_displays, message)).start()
        except socket.timeout:
            print(client_socket.gettimeout())
            server_status.style = ft.TextStyle(color="red")
            client_socket.settimeout(None)
            page.update()
        except Exception as e:
            print(f"接收消息时出错: {e}")

# 弹窗提示错误信息
def show_error_dialog(page, message):
    def close_dialog(e):
        error_dialog.open = False
        page.update()
    
    error_dialog = ft.AlertDialog(
        title=ft.Text("错误"),
        content=ft.Text(message),
        actions=[ft.TextButton("确定", on_click=close_dialog)],
    )
    page.dialog = error_dialog
    error_dialog.open = True
    page.update()

# 弹窗提示信息
def show_info_dialog(page,message):
    def close_dialog(e):
        info_dialog.open = False
        page.update()
    
    info_dialog = ft.AlertDialog(
        title=ft.Text("提示"),
        content=ft.Text(message),
        actions=[ft.TextButton("确定", on_click=close_dialog)],
    )
    page.dialog = info_dialog
    info_dialog.open = True
    page.update()

# 显示聊天界面
def show_chat_interface(page, username):
    # 设置超时时间为None
    client_socket.settimeout(None)

    global private_chat_displays, private_chat_tab, server_status, private_chat_tabs
    public_message_input = ft.TextField(label="公共消息")
    private_message_input = ft.TextField(label="私聊消息")
    public_chat_display = ft.Column() # 聊天显示区域
    private_chat_displays = {} # 私聊显示区域

    all_users = receive_all_users() # 获取在线用户列表

    def send_public_message(e):
        message = public_message_input.value
        print(f"PUBLIC {username} {message}")
        # 输出到公共聊天室
        public_chat_display.controls.append(ft.Text(f"{username}: {message}", style=ft.TextStyle(color="blue")))
        client_socket.sendto(f"PUBLIC {username} {message}".encode('utf-8'), server_address)
        public_message_input.value = ""
        page.update()

    def send_private_message(e):
        message = private_message_input.value
        receiver = private_chat_tabs[private_chat_tab.content.controls[3].selected_index].text
        print(f"PRIVATE {username} {receiver} {message}")
        # 输出到私聊界面
        private_chat_displays[receiver].controls.append(ft.Text(f"{username} (私聊): {message}", style=ft.TextStyle(color="blue")))
        client_socket.sendto(f"PRIVATE {username} {receiver} {message}".encode('utf-8'), server_address)
        private_message_input.value = ""
        page.update()
        

    # 公共聊天室选项卡
    public_chat_tab = ft.Tab(
        text="公共聊天室",
        content=ft.Column([
            ft.Text(f"欢迎，{username} - 公共聊天室"),
            public_message_input,
            ft.ElevatedButton(text="发送", on_click=send_public_message),
            public_chat_display
        ])
    )

    # 为每个用户在聊天界面添加一个选项卡
    private_chat_tabs = []
    for user,status in all_users.items():
        if user != username and status=='True':
            private_chat_displays[user] = ft.Column()
            private_chat_tabs.append(ft.Tab(text=user, content=private_chat_displays[user], icon=ft.Icon(name="check_circle")))
        elif user != username and status=='False':
            private_chat_displays[user] = ft.Column()
            private_chat_tabs.append(ft.Tab(text=user, content=private_chat_displays[user], icon=ft.Icon(name="error")))

    
    # 私聊选项卡
    private_chat_tab = ft.Tab(
        text="私聊",
        content=ft.Column([
            ft.Text(f"欢迎，{username} - 私聊"),
            private_message_input,
            ft.ElevatedButton(text="发送", on_click=send_private_message),
            ft.Tabs(tabs=private_chat_tabs)
        ])
    )

    # 服务器状态灯 与 刷新按钮
    server_status = ft.Text("服务器在线情况", style=ft.TextStyle(color="green"))
    refresh_button = ft.ElevatedButton(text="刷新")
    # 退出登录按钮
    logout_button = ft.ElevatedButton(text="退出登录")

    def logout(e):
        client_socket.sendto(f"EXIT {username}".encode('utf-8'), server_address)
    logout_button.on_click = logout

    def refresh(e):
        receive_all_users(0)
        check_server_online(0)
        page.update()
    refresh_button.on_click = refresh
    

    # 将登录界面清空，添加选项卡
    page.controls.clear()
     # 添加服务器状态灯和刷新按钮
    page.add(server_status, refresh_button, logout_button)
    page.add(ft.Tabs(tabs=[public_chat_tab, private_chat_tab]))
    page.update()

    # 接收消息
    threading.Thread(target=receive_messages, args=(page, public_chat_display, private_chat_displays)).start()

def main(page: ft.Page):
    global lock, username
    # 创建一个锁对象
    lock = threading.Lock()

    page.title = "UDP 聊天室"
    page.vertical_alignment = ft.MainAxisAlignment.START

    username_input = ft.TextField(label="用户名")
    password_input = ft.TextField(label="密码", password=True)

    def register(e):
        global username
        username = username_input.value
        password = password_input.value
        client_socket.sendto(f"REGISTER {username} {password}".encode('utf-8'), server_address)
        data, _ = client_socket.recvfrom(1024)
        # 注册成功,弹窗提示
        if data.decode('utf-8') == "注册成功":
            show_info_dialog(page,"注册成功")
        else:
            show_error_dialog(page, data.decode('utf-8'))
            

    def login(e):
        global username
        username = username_input.value
        password = password_input.value
        client_socket.sendto(f"LOGIN {username} {password}".encode('utf-8'), server_address)
        data, _ = client_socket.recvfrom(1024)
        if data.decode('utf-8') == "登录成功":
            show_chat_interface(page, username)
        else:
            show_error_dialog(page, data.decode('utf-8'))

    if check_server_online():
        page.add(
            ft.Text("服务器在线", style=ft.TextStyle(color="green")),
            username_input,
            password_input,
            ft.Row([ft.ElevatedButton(text="注册", on_click=register), ft.ElevatedButton(text="登录", on_click=login)])
        )
    else:
        page.add(ft.Text("服务器不在线，请启动服务器，并重启聊天室", style=ft.TextStyle(color="red")))

    page.update()

ft.app(target=main)
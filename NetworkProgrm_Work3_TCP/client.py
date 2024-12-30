import socket
import flet as ft

BET_TYPES = {
    "押头彩" : "tc",
    "押大彩" : "dc",
    "押空盘" : "kp",
    "押七星" : "qx",
    "押单对" : "dd",
    "押散星" : "sx",
}

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


def show_bet(page):
    page.controls.clear()

    # 接收服务器的欢迎消息
    welcome_message = client.recv(1024).decode('utf-8')
    print(welcome_message)
    # 规则展示控件
    welcome_area = ft.Column()
    welcome_area.controls.append(ft.Text(value=welcome_message))

    page.add(welcome_area)

    start_button = ft.ElevatedButton(text="开始游戏", on_click=lambda e: start_game())
    exit_button = ft.ElevatedButton(text="退出游戏", on_click=lambda e: exit_game())

    # 是否继续游戏
    continue_button = ft.ElevatedButton(text="继续游戏", on_click=lambda e: start_game())

    page.add(start_button, exit_button)
    page.update()

    output_area = ft.Column()

    def start_game():
        # 如果存在start_button和exit_button则删除
        if start_button in page.controls:
            page.controls.remove(start_button)
        if exit_button in page.controls:
            page.controls.remove(exit_button)
        if continue_button in page.controls:
            page.controls.remove(continue_button)
        if not output_area in page.controls:
            page.add(output_area)

        # 清空 继续游戏 后中output_area的内容
        output_area.controls.clear()

        page.update()
        # 发送开始游戏命令
        client.send("start".encode('utf-8'))
        # 输出初次投掷
        first_throw = client.recv(1024).decode('utf-8')
        print(first_throw)
        output_area.controls.append(ft.Text(value=first_throw))
        
        # 通过下拉框选择下注值
        bet_type = ft.Dropdown(label="下注类型", options=[ft.dropdown.Option("押头彩"), ft.dropdown.Option("押大彩"), ft.dropdown.Option("押空盘"), ft.dropdown.Option("押七星"), ft.dropdown.Option("押单对"), ft.dropdown.Option("押散星")], value="押头彩")
        bet_amount = ft.TextField(label="下注金额", value="1")
        bet_currency = ft.Dropdown(label="货币", options=[ft.dropdown.Option("coin"), ft.dropdown.Option("silver"), ft.dropdown.Option("gold")], value="coin")
        bet_button = ft.ElevatedButton(text="下注", on_click=lambda e: bet())

        page.add(bet_type, bet_amount, bet_currency, bet_button)
        page.update()

        def bet():
            # 发送下注命令到服务器
            bet_type_value = BET_TYPES[bet_type.value]
            bet_command = f"bet {bet_type_value} {bet_amount.value} {bet_currency.value}"
            client.send(bet_command.encode('utf-8'))

            # 接收服务器的结果
            result = client.recv(1024).decode('utf-8')
            # 更新添加结果
            output_area.controls.append(ft.Text(value=result))

            # 去除有关下注的控件
            page.controls.remove(bet_type)
            page.controls.remove(bet_amount)
            page.controls.remove(bet_currency)
            page.controls.remove(bet_button)

            page.add(continue_button, exit_button)
            page.update()

    def exit_game():
        # 发送退出游戏命令
        client.send("exit".encode('utf-8'))
        # 关闭客户端
        client.close()
        page.controls.clear()
        page.update()
        show_info_dialog(page,"游戏结束！")

def main(page:ft.Page):
    page.title = "RemoteBet 客户端"
    page.vertical_alignment = ft.MainAxisAlignment.START

    server_ip_input = ft.TextField(label="服务器IP地址", value="127.0.0.1")
    connect_button = ft.ElevatedButton(text="连接服务器", on_click=lambda e: connect_to_server())
    page.add(server_ip_input, connect_button)

    page.update()

    def connect_to_server():
        global server_ip, server_port, client
        server_ip = server_ip_input.value
        server_port = 9999
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((server_ip, server_port))
        except ConnectionRefusedError:
            show_error_dialog(page, "连接失败，请检查服务器是否已启动。")
            return
        show_bet(page)

ft.app(target=main)
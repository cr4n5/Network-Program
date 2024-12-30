import socket
import threading
import random

# 游戏规则和赔率
RULES = {
    'tc': 35,
    'dc': 17,
    'kp': 5,
    'qx': 5,
    'dd': 3,
    'sx': 2
}

NUMBER_TO_CHINESE = {
    1: '一',
    2: '二',
    3: '三',
    4: '四',
    5: '五',
    6: '六',
    7: '七',
    8: '八',
    9: '九',
    10: '十',
    11: '十一',
    12: '十二'
}

# 初始化骰子
dice_tpl= '''\
┌───┐,┌───┐,┌───┐,┌───┐,┌───┐,┌───┐
│      │,│  ●  │,│●    │,│●  ●│,│●  ●│,│●  ●│
│  ●  │,│      │,│  ●  │,│      │,│  ●  │,│●  ●│
│      │,│  ●  │,│    ●│,│●  ●│,│●  ●│,│●  ●│
└───┘,└───┘,└───┘,└───┘,└───┘,└───┘'''

dice_lines = dice_tpl.split('\n')

#补充完整下面的代码
dice_lines[0]=dice_lines[0].split(',')
dice_lines[1]=dice_lines[1].split(',')
dice_lines[2]=dice_lines[2].split(',')
dice_lines[3]=dice_lines[3].split(',')
dice_lines[4]=dice_lines[4].split(',')
dice=[]
for i in range(6):
    dice.append(dice_lines[0][i]+"\n"+dice_lines[1][i]+"\n"+dice_lines[2][i]+"\n"+dice_lines[3][i]+"\n"+dice_lines[4][i])

WELCOME_MESSAGE='''
 规则如下：
    ya tc <数量> <coin|silver|gold> 押头彩(两数顺序及点数均正确)       一赔三十五
    ya dc <数量> <coin|silver|gold> 押大彩(两数点数正确)               一赔十七
    ya kp <数量> <coin|silver|gold> 押空盘(两数不同且均为偶数)         一赔五
    ya qx <数量> <coin|silver|gold> 押七星(两数之和为七)               一赔五
    ya dd <数量> <coin|silver|gold> 押单对(两数均为奇数)               一赔三
    ya sx <数量> <coin|silver|gold> 押散星(两数之和为三、五、九、十一)   一赔二

每盘按从上到下的顺序只出现一种点型(头彩和大彩可同时出现)，其他情况都算庄家赢。
'''


# 处理客户端连接
def handle_client(client_socket):
    client_socket.send(WELCOME_MESSAGE.encode('utf-8'))
    while True:
        # 接收客户端的开始游戏命令
        start_message = client_socket.recv(1024).decode('utf-8').strip()
        print(start_message)
        if not start_message:
            break
        if start_message.lower() == 'exit':
            break

        send_message = '庄家唱道：新开盘！预叫头彩！\n庄家将两枚玉骰往银盘中一撒。\n'
        # 初始投掷
        dice1_origin = random.randint(1, 6)
        dice2_origin = random.randint(1, 6)
        send_message += dice[dice1_origin-1]+"\n"
        send_message += dice[dice2_origin-1]+"\n"
        send_message +="庄家唱道：头彩骰号是{}、{}！".format(NUMBER_TO_CHINESE[dice1_origin],NUMBER_TO_CHINESE[dice2_origin])
        # 发送骰子结果,转成中文数字
        client_socket.send(send_message.encode('utf-8'))
        # 接收客户端的下注
        bet = client_socket.recv(1024).decode('utf-8').strip()
        if not bet:
            break
        
        # 解析下注命令
        try:
            _, bet_type, amount, currency = bet.split()
            amount = int(amount)
        except ValueError:
            client_socket.send("无效的下注命令，请重新输入。\n".encode('utf-8'))
            continue
            
        send_message = ""
        # 骰子结果
        send_message += "庄家将两枚玉骰扔进两个金盅，一手持一盅摇将起来。\n庄家将左手的金盅倒扣在银盘上，玉骰滚了出来。\n"
        dice1 = random.randint(1, 6)
        send_message += dice[dice1-1]+"\n"
        send_message += "庄家将右手的金盅倒扣在银盘上，玉骰滚了出来。\n"
        dice2 = random.randint(1, 6)
        send_message += dice[dice2-1]+"\n"
        result = (dice1, dice2)
        send_message += "庄家叫道：{}、{}……{}星。\n".format(NUMBER_TO_CHINESE[dice1],NUMBER_TO_CHINESE[dice2],NUMBER_TO_CHINESE[dice1+dice2])
        
        # 计算结果
        payout = calculate_payout(bet_type, result, amount,dice1_origin,dice2_origin)
        
        if payout > 0:
            send_message += f"你赢了{payout} {currency}！\n"
        else:
            send_message += f"你输了！{amount} {currency}\n"
        client_socket.send(send_message.encode('utf-8'))
    
    client_socket.close()

# 计算赔率
def calculate_payout(bet_type, result, amount,dice1_origin,dice2_origin):
    dice1, dice2 = result
    if bet_type == 'tc' and dice1 == dice1_origin and dice2 == dice2_origin:
        return amount * RULES[bet_type]
    elif bet_type == 'dc' and ((dice1 == dice1_origin and dice2 == dice2_origin) or (dice1 == dice2_origin and dice2 == dice1_origin)):
        return amount * RULES[bet_type]
    elif bet_type == 'kp' and dice1 % 2 == 0 and dice2 % 2 == 0 and dice1 != dice2:
        return amount * RULES[bet_type]
    elif bet_type == 'qx' and dice1 + dice2 == 7:
        return amount * RULES[bet_type]
    elif bet_type == 'dd' and dice1 % 2 == 1 and dice2 % 2 == 1:
        return amount * RULES[bet_type]
    elif bet_type == 'sx' and dice1 + dice2 in [3, 5, 9, 11]:
        return amount * RULES[bet_type]
    else:
        return 0

# 启动服务器
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    print("服务器启动，等待连接...")
    
    while True:
        client_socket, addr = server.accept()
        print(f"接受到来自{addr}的连接")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_server()
import flet as ft
import socket
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import time

class FileServer:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback
        self.running = False
        self.server = None
        self.executor = None
        self.clients = {}
        
    def update_status(self, addr, message=None, progress=None, speed=None):
        if self.status_callback:
            self.status_callback(addr, message, progress, speed)
            
    def handle_client(self, client_socket, addr):
        """处理单个客户端连接"""
        self.clients[addr] = {"progress": 0, "speed": 0}
        self.update_status(addr, f"客户端连接: {addr}")
        
        try:
            filepath = client_socket.recv(1024).decode()
            self.update_status(addr, f"客户端 {addr} 请求: {filepath}")
            
            if not os.path.exists(filepath):
                client_socket.send("FILE_NOT_FOUND".encode())
                return
                
            file_size = os.path.getsize(filepath)
            client_socket.send(str(file_size).encode())
            
            start_time = time.time()
            sent_size = 0
            with open(filepath, 'rb') as f:
                while sent_size < file_size:
                    data = f.read(1024*1024)
                    if not data:
                        break
                    client_socket.send(data)
                    sent_size += len(data)
                    progress = sent_size / file_size
                    elapsed_time = time.time() - start_time
                    if elapsed_time == 0:
                        elapsed_time = 1e-10  # 设置一个非常小的值以避免除以零
                    speed = sent_size / (1024 * 1024 * elapsed_time)
                    self.update_status(
                        addr,
                        None,  # 不更新消息
                        progress,
                        speed
                    )
                    
        except Exception as e:
            self.update_status(addr, f"错误 {addr}: {str(e)}")
        finally:
            client_socket.close()
            del self.clients[addr]
            self.update_status(addr, f"客户端断开: {addr}")
            
    def start(self, host, port):
        if self.running:
            return
            
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        def accept_connections():
            while self.running:
                try:
                    client_socket, addr = self.server.accept()
                    self.executor.submit(self.handle_client, client_socket, addr)
                except:
                    break
                    
        self.accept_thread = threading.Thread(target=accept_connections)
        self.accept_thread.start()
        
    def stop(self):
        self.running = False
        if self.server:
            self.server.close()
        if self.executor:
            self.executor.shutdown(wait=True)
        for client in self.clients.copy():
            try:
                client.close()
            except:
                pass

class ServerApp:
    def __init__(self):
        self.server = FileServer(self.update_status)
        self.client_progress_bars = {}
        self.client_speed_texts = {}
        
    def main(self, page: ft.Page):
        self.page = page
        page.title = "文件服务器"
        # page.window_width = 600
        # page.window_height = 500
        # page.padding = 20
        
        # 根据控件自动调整窗口大小
        page.auto_size = True
        
        # UI组件
        self.host_input = ft.TextField(
            label="服务器地址",
            value="localhost",
            width=200
        )
        self.port_input = ft.TextField(
            label="端口",
            value="9999",
            width=200
        )
        
        self.status_text = ft.Text("服务器未启动")
        
        # 修改日志视图的实现
        self.log_view = ft.ListView(
            expand=True,
            spacing=10,
            height=300,
        )

        # 使用Container包装ListView并添加边框
        log_container = ft.Container(
            content=self.log_view,
            border=ft.border.all(1),
            padding=10,
            expand=True
        )
        
        self.start_button = ft.ElevatedButton(
            text="启动服务器",
            on_click=self.toggle_server
        )
        
        # 布局
        page.add(
            ft.Row([self.host_input, self.port_input]),
            self.start_button,
            self.status_text,
            ft.Text("服务器日志:"),
            log_container  # 使用包装后的容器
        )
        
    def update_status(self, addr, message=None, progress=None, speed=None):
        if message:
            self.log_view.controls.append(ft.Text(f"[{time.strftime('%H:%M:%S')}] {message}"))
        if len(self.log_view.controls) > 100:
            self.log_view.controls.pop(0)
        
        if addr not in self.client_progress_bars:
            self.client_progress_bars[addr] = ft.ProgressBar(width=400, visible=True)
            self.client_speed_texts[addr] = ft.Text(f"客户端 {addr} 速度: 0 MB/s")
            self.page.add(self.client_progress_bars[addr], self.client_speed_texts[addr])

            # 最多显示5个客户端的进度条
            if len(self.client_progress_bars) > 5:
                addr_to_remove = list(self.client_progress_bars.keys())[0]
                self.page.remove(self.client_progress_bars[addr_to_remove])
                self.page.remove(self.client_speed_texts[addr_to_remove])
                del self.client_progress_bars[addr_to_remove]
                del self.client_speed_texts[addr_to_remove]
        
        if progress is not None:
            self.client_progress_bars[addr].value = progress
            self.client_speed_texts[addr].value = f"客户端 {addr} 速度: {speed:.2f} MB/s"
        
        self.page.update()
        
    def toggle_server(self, e):
        if not self.server.running:
            self.server.start(self.host_input.value, int(self.port_input.value))
            self.start_button.text = "停止服务器"
            self.status_text.value = "服务器运行中"
            self.host_input.disabled = True
            self.port_input.disabled = True
        else:
            self.server.stop()
            self.start_button.text = "启动服务器"
            self.status_text.value = "服务器已停止"
            self.host_input.disabled = False
            self.port_input.disabled = False
            
        self.page.update()

if __name__ == "__main__":
    app = ServerApp()
    ft.app(target=app.main)
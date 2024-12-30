import flet as ft
import socket
import os
import time
from typing import Callable

class FileDownloader:
    def __init__(self, progress_callback: Callable = None):
        self.progress_callback = progress_callback
        
    def download_file(self, host: str, port: int, remote_file: str, local_file: str):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            
            client.send(remote_file.encode())
            response = client.recv(1024).decode()
            
            if response == "FILE_NOT_FOUND":
                return "错误: 文件在服务器上不存在"
            
            file_size = int(response)
            received_size = 0
            start_time = time.time()
            
            with open(local_file, 'wb') as f:
                while received_size < file_size:
                    data = client.recv(min(1024*1024, file_size - received_size))
                    if not data:
                        break
                    f.write(data)
                    received_size += len(data)
                    
                    # 更新进度
                    if self.progress_callback:
                        progress = (received_size / file_size) * 100
                        elapsed_time = time.time() - start_time
                        if elapsed_time == 0:
                            elapsed_time = 1e-10  # 设置一个非常小的值以避免除以零
                        speed = received_size / (1024 * 1024 * elapsed_time)
                        self.progress_callback(progress, speed)
            
            duration = time.time() - start_time
            if duration == 0:
                duration = 1e-10
            speed = file_size / (1024 * 1024 * duration)
            return f"下载完成! 用时: {duration:.2f}秒, 平均速度: {speed:.2f} MB/s"
            
        except ConnectionRefusedError:
            return "错误: 无法连接到服务器"
        except Exception as e:
            return f"下载出错: {e}"
        finally:
            client.close()

class DownloadApp:
    def __init__(self):
        self.downloader = FileDownloader(self.update_progress)
        self.dialog = None
        self.page = None  # 添加page属性
        
    def main(self, page: ft.Page):
        self.page = page  # 保存page引用
        page.title = "文件下载客户端"
        page.window_width = 600
        page.window_height = 400
        page.padding = 20
        
        # UI组件
        self.host_input = ft.TextField(label="服务器地址", value="localhost")
        self.port_input = ft.TextField(label="端口", value="9999")
        self.remote_file = ft.TextField(label="远程文件路径")
        self.local_file = ft.TextField(label="本地保存路径")
        
        self.progress_bar = ft.ProgressBar(width=400, visible=False)
        self.status_text = ft.Text("")
        self.download_button = ft.ElevatedButton(
            text="开始下载",
            on_click=self.start_download
        )
        
        # 布局
        page.add(
            ft.Column([
                self.host_input,
                self.port_input,
                self.remote_file,
                self.local_file,
                self.download_button,
                self.progress_bar,
                self.status_text
            ])
        )
    
    def update_progress(self, progress: float, speed: float):
        self.progress_bar.value = progress / 100
        self.status_text.value = f"进度: {progress:.1f}%, 速度: {speed:.2f} MB/s"
        # 更新页面以显示进度
        self.page.update()
    
    # 开始下载按钮点击事件
    def start_download(self, e):
        # 检查输入
        if not all([self.host_input.value, self.port_input.value, 
                   self.remote_file.value, self.local_file.value]):
            self.status_text.value = "请填写所有字段"
            return
        
        # 检查文件是否存在
        if os.path.exists(self.local_file.value):
            self.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("文件已存在"),
                content=ft.Text("是否覆盖已存在的文件?"),
                actions=[
                    ft.TextButton("取消", on_click=self.close_dialog),
                    ft.TextButton("确定", on_click=self.confirm_and_close_dialog)
                ]
            )
            self.page.open(self.dialog)
            return
        
        self.do_download()
    
    def close_dialog(self, e):
        self.page.close(self.dialog)
    
    def confirm_and_close_dialog(self, e):
        self.page.close(self.dialog)
        self.do_download()

    def confirm_download(self, e):
        self.do_download()
    
    def do_download(self):
        self.download_button.disabled = True
        self.progress_bar.visible = True
        
        result = self.downloader.download_file(
            self.host_input.value,
            int(self.port_input.value),
            self.remote_file.value,
            self.local_file.value
        )
        
        self.status_text.value = result
        self.download_button.disabled = False
        self.progress_bar.visible = False
        self.page.update()

if __name__ == "__main__":
    app = DownloadApp()
    ft.app(target=app.main)
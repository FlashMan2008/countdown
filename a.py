import configparser
import datetime
import time
import threading
import tkinter as tk
from tkinter import scrolledtext
from pystray import Icon, MenuItem, Menu
from PIL import Image
import pygame
from pydub import AudioSegment
import sys
import os
import uuid

class App:
    def __init__(self):
        # 初始化日志文件路径
        self.log_file_path = "app_log.txt"
        self.setup_log_file()
        
        # 创建日志窗口
        self.create_log_window()

        # 创建托盘图标
        self.tray_icon = self.create_tray_icon()
        self.tray_running = False
        self.start_tray_icon()

    def setup_log_file(self):
        """
        设置日志文件
        """
        # 清空文件内容以便重新记录日志
        with open(self.log_file_path, 'w') as log_file:
            log_file.write("日志文件创建成功。\n")

    def write_log(self, message):
        """
        向日志窗口和日志文件中输出信息，替代 print 函数
        """
        # 使用 after 确保在主线程中更新日志窗口
        self.log_window.after(0, self._update_log_window, message)
        
        # 输出到日志文件
        try:
            with open(self.log_file_path, 'a') as log_file:
                log_file.write(message + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}")

    def _update_log_window(self, message):
        """
        更新日志窗口的实际实现
        """
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state='disabled')  # 禁止手动编辑日志
        self.log_text.see(tk.END)  # 滚动到最新行

    def create_log_window(self):
        """
        创建一个用于显示输出信息的日志窗口
        """
        self.log_window = tk.Tk()
        self.log_window.title("后台运行日志")
        self.log_window.geometry("400x300")
        self.log_window.protocol("WM_DELETE_WINDOW", self.on_closing_log_window)  # 捕获关闭日志窗口的事件

        # 创建一个滚动文本框，用于显示日志信息
        self.log_text = scrolledtext.ScrolledText(self.log_window, wrap=tk.WORD, state='disabled')
        self.log_text.pack(expand=True, fill='both')

        # 输出程序正在后台运行的提示
        self.write_log("程序正在后台运行。")

    def create_tray_icon(self):
        """
        创建系统托盘图标
        """
        # 创建一个简单的图标
        image = Image.open("icon.png")

        # 创建菜单
        menu = Menu(MenuItem("Restore", self.show_log_window), 
                    MenuItem("Exit", self.exit_app))

        # 创建托盘图标对象
        tray_icon = Icon("AppTray", image, "倒计时程序", menu)
        return tray_icon

    def start_tray_icon(self):
        """
        启动托盘图标
        """
        if not self.tray_running:
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
            self.tray_running = True

    def stop_tray_icon(self):
        """
        停止托盘图标
        """
        if self.tray_running:
            try:
                self.tray_icon.stop()
            except Exception as e:
                self.write_log(f"Error stopping tray icon: {e}")
            self.tray_running = False

    def minimize_to_tray(self):
        """
        最小化到托盘
        """
        self.hide_log_window()

    def hide_log_window(self):
        """
        隐藏日志窗口
        """
        self.log_window.withdraw()  # 隐藏窗口

    def show_log_window(self, icon, item):
        """
        从托盘中恢复日志窗口
        """
        self.log_window.deiconify()  # 恢复窗口

    def exit_app(self, icon, item):
        """
        退出应用
        """
        self.write_log("退出应用...")
        self.stop_tray_icon()  # 停止托盘图标
        self.log_window.after(0, self.close_application)

    def close_application(self):
        """
        关闭应用程序
        """
        self.log_window.quit()  # 关闭日志窗口
        sys.exit()  # 确保程序完全退出

    def on_closing_log_window(self):
        """
        关闭日志窗口时最小化到托盘，而不是退出程序
        """
        self.minimize_to_tray()

def show_countdown(countdown_seconds):
    """
    显示一个全屏窗口来进行倒计时。
    
    :param countdown_seconds: 倒计时的秒数
    """
    try:
        # 创建一个 Tkinter 主窗口
        root = tk.Tk()
        root.attributes("-fullscreen", True)  # 设置窗口为全屏
        root.attributes("-topmost", True)     # 设置窗口置顶
        root.configure(bg='black')  # 设置窗口背景为黑色

        # 创建一个标签用于显示倒计时，设置为白色字体和黑色背景
        countdown_label = tk.Label(root, font=('Helvetica', 120), fg='white', bg='black')
        countdown_label.pack(expand=True)

        def countdown(count):
            """
            更新倒计时显示。
            
            :param count: 当前倒计时秒数
            """
            if count >= 0:
                countdown_label.config(text=str(count))
                root.after(1000, countdown, count - 1)  # 每秒递减倒计时
            else:
                root.after(100, lambda: root.destroy())  # 在主线程中安全地关闭窗口

        countdown(countdown_seconds)  # 开始倒计时
        root.mainloop()
    except Exception as e:
        app.write_log(f"Error in countdown display: {e}")

def preload_audio(audio_file_path):
    """
    预加载音频文件并返回音频数据
    :param audio_file_path: 音频文件路径
    """
    try:
        # 使用 pydub 加载音频文件并返回音频片段
        audio = AudioSegment.from_file(audio_file_path)
        return audio
    except Exception as e:
        app.write_log(f"Error preloading audio: {e}")
        return None

def play_preloaded_audio(audio, countdown_seconds):
    """
    播放预加载的音频文件，使用唯一的临时文件避免冲突
    :param audio: 预加载的音频数据
    :param countdown_seconds: 倒计时时间，决定从音频的倒数几秒开始播放
    """
    try:
        # 初始化 pygame 的混音器
        pygame.mixer.init()

        # 使用唯一的临时文件名
        temp_audio_file = f"temp_audio_{uuid.uuid4()}.wav"
        
        # 截取音频倒数 countdown_seconds 的部分
        start_time_ms = len(audio) - (countdown_seconds * 1000) + 300
        audio_to_play = audio[start_time_ms:]
        
        # 导出为临时音频文件
        audio_to_play.export(temp_audio_file, format="wav")
        
        # 播放音频
        pygame.mixer.music.load(temp_audio_file)
        pygame.mixer.music.play()

        # 等待音频播放完成
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # 停止并释放 pygame 资源
        pygame.mixer.music.stop()
        pygame.mixer.quit()

        # 删除临时文件
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)

    except Exception as e:
        app.write_log(f"Error playing preloaded audio: {e}")

def play_audio_and_show_countdown(audio, countdown_seconds):
    """
    同时播放预加载的音频文件和显示倒计时窗口，倒计时时长为 countdown_seconds。
    
    :param audio: 预加载的音频数据
    :param countdown_seconds: 倒计时时长
    """
    try:
        # 创建一个线程来播放音频
        audio_thread = threading.Thread(target=play_preloaded_audio, args=(audio, countdown_seconds))
        audio_thread.start()

        # 显示倒计时窗口
        show_countdown(countdown_seconds)
    except Exception as e:
        app.write_log(f"Error in countdown or audio playback: {e}")

def adjust_time_by_seconds(target_time, countdown_seconds):
    """
    将目标时间提前 countdown_seconds 秒。
    
    :param target_time: 原始目标时间，datetime.datetime 对象
    :param countdown_seconds: 要提前的秒数
    :return: 提前后的目标时间，datetime.datetime 对象
    """
    adjusted_time = target_time - datetime.timedelta(seconds=countdown_seconds)
    return adjusted_time

def check_time_and_trigger(audio, target_time, countdown_seconds):
    """
    在指定的时间（精确到秒）触发音频播放和倒计时显示。
    
    :param audio: 预加载的音频数据
    :param target_time: 目标时间，格式为 'HH:MM:SS'，例如 '14:30:15'
    :param countdown_seconds: 倒计时时长
    """
    target_hour, target_minute, target_second = map(int, target_time.split(':'))
    now = datetime.datetime.now()
    target_time_obj = now.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)
    
    adjusted_time = adjust_time_by_seconds(target_time_obj, countdown_seconds)
    
    while True:
        current_time = datetime.datetime.now()
        # 当当前时间精确到秒等于设定的时间时，开始播放音频和倒计时
        if (current_time.hour == adjusted_time.hour and
            current_time.minute == adjusted_time.minute and
            current_time.second == adjusted_time.second):
            try:
                app.write_log(f"提前 {countdown_seconds} 秒到达指定时间 {target_time}，正在播放音频并显示倒计时...")
                play_audio_and_show_countdown(audio, countdown_seconds)
            except Exception as e:
                app.write_log(f"Error triggering countdown: {e}")
            break
        time.sleep(0.5)  # 更新间隔

def run_in_background(audio, target_times, countdown_seconds):
    """
    启动多个后台线程来分别在多个时间播放音频和显示倒计时窗口。
    
    :param audio: 预加载的音频数据
    :param target_times: 目标时间的列表，每个时间的格式为 'HH:MM:SS'
    :param countdown_seconds: 倒计时时长
    """
    for target_time in target_times:
        background_thread = threading.Thread(target=check_time_and_trigger, args=(audio, target_time, countdown_seconds))
        background_thread.daemon = True
        background_thread.start()

def read_settings_from_ini(file_path='settings.ini'):
    """
    从 settings.ini 文件中读取配置。
    
    :param file_path: 配置文件路径
    :return: 返回音频文件路径、时间列表和倒计时时长
    """
    config = configparser.ConfigParser()
    config.read(file_path)
    audio_file_path = config.get('Settings', 'audio_file_path')
    alarm_times = config.get('Settings', 'alarm_times')
    countdown_seconds = int(config.get('Settings', 'countdown_seconds', fallback='10'))
    alarm_time_list = [time.strip() for time in alarm_times.split(',')]
    return audio_file_path, alarm_time_list, countdown_seconds

# 从配置文件读取设置
audio_path, alarm_times, countdown_seconds = read_settings_from_ini('settings.ini')

# 预加载音频文件
audio_data = preload_audio(audio_path)

# 创建主应用实例
app = App()

# 运行程序
run_in_background(audio_data, alarm_times, countdown_seconds)

# 主线程保持运行，日志窗口显示所有信息
app.write_log("程序已经开始运行，等待触发器执行。")
app.log_window.mainloop()

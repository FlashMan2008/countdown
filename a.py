import configparser
import datetime
import time
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from pystray import Icon, MenuItem, Menu
from PIL import Image
import pygame
from pydub import AudioSegment
import sys
import os
import uuid

# 全局存储所有后台线程及其停止事件
background_threads = []

class App:
    def __init__(self):
        self.log_file_path = "app_log.txt"
        self.setup_log_file()
        self.create_log_window()
        self.tray_icon = self.create_tray_icon()
        self.tray_running = False
        self.start_tray_icon()
        self.settings_window = None
        self.alarm_shutdown_list = []

    def setup_log_file(self):
        with open(self.log_file_path, 'a') as log_file:
            log_file.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")

    def write_log(self, message):
        self.log_window.after(0, self._update_log_window, message)
        with open(self.log_file_path, 'a') as log_file:
            log_file.write(message + "\n")

    def _update_log_window(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

    def create_log_window(self):
        self.log_window = tk.Tk()
        self.log_window.title("后台运行日志")
        self.log_window.geometry("400x300")
        self.log_window.protocol("WM_DELETE_WINDOW", self.on_closing_log_window)
        self.log_window.iconbitmap("icon.ico")
        self.log_text = scrolledtext.ScrolledText(self.log_window, wrap=tk.WORD, state='disabled')
        self.log_text.pack(expand=True, fill='both')
        self.write_log("程序正在后台运行。")

    def create_tray_icon(self):
        image = Image.open("icon.ico")
        menu = Menu(
            MenuItem("Show Log", self.show_log_window),
            MenuItem("Settings", self.open_settings_window),
            MenuItem("Exit", self.exit_app)
        )
        tray_icon = Icon("AppTray", image, "倒计时程序", menu)
        return tray_icon

    def start_tray_icon(self):
        if not self.tray_running:
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
            self.tray_running = True

    def stop_tray_icon(self):
        if self.tray_running:
            try:
                self.tray_icon.stop()
            except Exception as e:
                self.write_log(f"Error stopping tray icon: {e}")
            self.tray_running = False

    def minimize_to_tray(self):
        self.hide_log_window()

    def hide_log_window(self):
        self.log_window.withdraw()

    def show_log_window(self, icon, item):
        self.log_window.deiconify()

    def open_settings_window(self, icon, item):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = tk.Toplevel(self.log_window)
            self.settings_window.title("Settings")
            self.settings_window.geometry("300x350")
            self.settings_window.iconbitmap("icon.ico")
            
            tk.Label(self.settings_window, text="音频文件路径:").pack(pady=(10,0))
            self.audio_path_entry = tk.Entry(self.settings_window)
            self.audio_path_entry.pack()
            
            tk.Label(self.settings_window, text="倒计时秒数:").pack(pady=(10,0))
            self.countdown_entry = tk.Entry(self.settings_window)
            self.countdown_entry.pack()
            
            tk.Label(self.settings_window, text="关机倒计时秒数:").pack(pady=(10,0))
            self.shutdown_countdown_entry = tk.Entry(self.settings_window)
            self.shutdown_countdown_entry.pack()

            tk.Label(self.settings_window, text="闹钟时间及关机设置:").pack(pady=(20,0))
            tk.Button(self.settings_window, text="设置", command=self.open_alarm_settings_window).pack(pady=5)

            self.audio_path_entry.insert(0, audio_path)
            self.countdown_entry.insert(0, str(countdown_seconds))
            self.shutdown_countdown_entry.insert(0, str(shutdown_countdown_seconds))

            tk.Button(self.settings_window, text="保存设置", command=self.save_settings).pack(pady=15)

    def open_alarm_settings_window(self):
        self.alarm_window = tk.Toplevel(self.settings_window)
        self.alarm_window.title("闹钟设置")
        self.alarm_window.geometry("400x300")
        
        # 主框架容器
        main_frame = tk.Frame(self.alarm_window)
        main_frame.pack(fill="both", expand=True)
        
        # 创建Canvas和滚动条
        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局组件
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 可滚动内容框架
        content_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # 配置滚动区域
        def _configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        content_frame.bind("<Configure>", _configure_canvas)
        
        # 鼠标滚轮支持
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 表头
        header_frame = tk.Frame(content_frame)
        header_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(header_frame, text="闹钟时间", width=20).grid(row=0, column=0)
        tk.Label(header_frame, text="关机标志", width=20).grid(row=0, column=1)
        tk.Label(header_frame, text="操作", width=10).grid(row=0, column=2)
        
        # 初始化现有行
        self.alarm_settings_rows = []
        for alarm_time, flag in self.alarm_shutdown_list:
            self.add_alarm_setting_row(alarm_time, flag, content_frame, False)
        
        # 控制按钮区域
        control_frame = tk.Frame(self.alarm_window)
        control_frame.pack(side="bottom", pady=5)
        
        tk.Button(control_frame, text="添加", 
                 command=lambda: self.add_alarm_setting_row("", 0, content_frame, True)
                ).pack(side='left', padx=5)
        tk.Button(control_frame, text="保存", command=self.save_alarm_settings).pack(side='left', padx=5)
        tk.Button(control_frame, text="取消", command=self.alarm_window.destroy).pack(side='left', padx=5)

    def add_alarm_setting_row(self, alarm_time, flag, parent, is_new):
        row_frame = tk.Frame(parent)
        row_frame.pack(fill='x', padx=5, pady=2, anchor='w')
        
        time_entry = tk.Entry(row_frame, width=20)
        time_entry.insert(0, alarm_time)
        time_entry.grid(row=0, column=0, padx=5)
        
        flag_entry = tk.Entry(row_frame, width=20)
        flag_entry.insert(0, str(flag))
        flag_entry.grid(row=0, column=1, padx=5)
        
        del_button = tk.Button(
            row_frame, 
            text="删除", 
            command=lambda: self.delete_alarm_setting_row(row_frame)
        )
        del_button.grid(row=0, column=2, padx=5)
        
        self.alarm_settings_rows.append((row_frame, time_entry, flag_entry, is_new))
        
        # 自动滚动到底部（修正后的层级引用）
        if is_new:
            # 正确的Canvas引用路径：row_frame -> content_frame (parent) -> canvas
            canvas = parent.master  # parent是content_frame，其master是canvas
            canvas.yview_moveto(1.0)

    def delete_alarm_setting_row(self, row_frame):
        for row in self.alarm_settings_rows:
            if row[0] == row_frame:
                row_frame.destroy()
                self.alarm_settings_rows.remove(row)
                self.alarm_window.update_idletasks()
                break

    def save_alarm_settings(self):
        new_list = []
        for row_frame, time_entry, flag_entry, _ in self.alarm_settings_rows:
            alarm_time = time_entry.get().strip()
            flag_str = flag_entry.get().strip()
            if alarm_time == "" or flag_str == "":
                continue
            try:
                flag = int(flag_str)
                datetime.datetime.strptime(alarm_time, "%H:%M:%S")
                new_list.append((alarm_time, flag))
            except ValueError as e:
                messagebox.showerror("错误", f"无效输入: {str(e)}")
                return
        self.alarm_shutdown_list = new_list
        self.alarm_window.destroy()

    def save_settings(self):
        audio_file_path = self.audio_path_entry.get()
        try:
            countdown_seconds_val = int(self.countdown_entry.get())
        except ValueError:
            self.write_log("倒计时秒数必须是整数。")
            return
        try:
            shutdown_countdown_val = int(self.shutdown_countdown_entry.get())
        except ValueError:
            self.write_log("关机倒计时秒数必须是整数。")
            return

        config = configparser.ConfigParser()
        config['Settings'] = {
            'audio_file_path': audio_file_path,
            'countdown_seconds': str(countdown_seconds_val),
            'shutdown_countdown_seconds': str(shutdown_countdown_val),
            'alarm_times': ', '.join([item[0] for item in self.alarm_shutdown_list]),
            'shutdown_after_alarm': ', '.join([str(item[1]) for item in self.alarm_shutdown_list])
        }
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)

        global background_threads
        for thread, stop_event in background_threads:
            stop_event.set()
        background_threads.clear()

        new_audio_data = preload_audio(audio_file_path)
        new_alarm_times = [item[0] for item in self.alarm_shutdown_list]
        new_shutdown_after = [item[1] for item in self.alarm_shutdown_list]
        run_in_background(new_audio_data, new_alarm_times, countdown_seconds_val, new_shutdown_after, shutdown_countdown_val)
        self.write_log("设置已更新，无需重启，新的计时线程已启动。")

    def exit_app(self, icon, item):
        self.write_log("退出应用...")
        self.stop_tray_icon()
        self.log_window.after(0, self.close_application)

    def close_application(self):
        self.log_window.quit()
        sys.exit()

    def on_closing_log_window(self):
        self.minimize_to_tray()

def show_shutdown_countdown(shutdown_countdown):
    root2 = tk.Tk()
    root2.attributes("-topmost", True)
    root2.overrideredirect(True)
    width, height = 300, 100
    screen_width = root2.winfo_screenwidth()
    screen_height = root2.winfo_screenheight()
    x = screen_width - width - 10
    y = screen_height - height - 10
    root2.geometry(f"{width}x{height}+{x}+{y}")
    label = tk.Label(root2, font=('Helvetica', 16), fg='white', bg='black')
    label.pack(expand=True, fill='both')
    def shutdown_countdown_func(count):
        if count >= 0:
            label.config(text=f"电脑将在 {count} 秒后关机")
            root2.after(1000, shutdown_countdown_func, count - 1)
        else:
            root2.destroy()
            os.system("shutdown /s /t 0")
    shutdown_countdown_func(shutdown_countdown)
    root2.mainloop()

def show_countdown(countdown_seconds, shutdown_enabled=False, shutdown_countdown=0):
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.configure(bg='black')
    if shutdown_enabled:
        shutdown_label = tk.Label(root, text="电脑即将关机", font=('Helvetica', 60), fg='red', bg='black')
        shutdown_label.pack(pady=(50, 10))
    countdown_label = tk.Label(root, font=('Helvetica', 120), fg='white', bg='black')
    countdown_label.pack(expand=True)
    def countdown(count):
        if count >= 0:
            countdown_label.config(text=str(count))
            root.after(1000, countdown, count - 1)
        else:
            root.destroy()
            if shutdown_enabled:
                show_shutdown_countdown(shutdown_countdown)
    countdown(countdown_seconds)
    root.mainloop()

def preload_audio(audio_file_path):
    try:
        audio = AudioSegment.from_file(audio_file_path)
        return audio
    except Exception as e:
        app.write_log(f"Error preloading audio: {e}")
        return None

def play_preloaded_audio(audio, countdown_seconds):
    try:
        pygame.mixer.init()
        temp_audio_file = f"temp_audio_{uuid.uuid4()}.wav"
        start_time_ms = len(audio) - (countdown_seconds * 1000) + 300
        audio_to_play = audio[start_time_ms:]
        audio_to_play.export(temp_audio_file, format="wav")
        pygame.mixer.music.load(temp_audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)
    except Exception as e:
        app.write_log(f"Error playing preloaded audio: {e}")

def play_audio_and_show_countdown(audio, countdown_seconds, shutdown_enabled, shutdown_countdown):
    try:
        audio_thread = threading.Thread(target=play_preloaded_audio, args=(audio, countdown_seconds))
        audio_thread.start()
        show_countdown(countdown_seconds, shutdown_enabled, shutdown_countdown)
    except Exception as e:
        app.write_log(f"Error in countdown or audio playback: {e}")

def adjust_time_by_seconds(target_time, countdown_seconds):
    return target_time - datetime.timedelta(seconds=countdown_seconds)

def check_time_and_trigger(audio, target_time, countdown_seconds, shutdown_enabled, shutdown_countdown, stop_event):
    target_hour, target_minute, target_second = map(int, target_time.split(':'))
    now = datetime.datetime.now()
    target_time_obj = now.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)
    adjusted_time = adjust_time_by_seconds(target_time_obj, countdown_seconds)
    while not stop_event.is_set():
        current_time = datetime.datetime.now()
        if (current_time.hour == adjusted_time.hour and
            current_time.minute == adjusted_time.minute and
            current_time.second == adjusted_time.second):
            try:
                app.write_log(f"提前 {countdown_seconds} 秒到达指定时间 {target_time}，正在播放音频并显示倒计时...")
                play_audio_and_show_countdown(audio, countdown_seconds, shutdown_enabled, shutdown_countdown)
            except Exception as e:
                app.write_log(f"Error triggering countdown: {e}")
            break
        time.sleep(0.5)

def run_in_background(audio, target_times, countdown_seconds, shutdown_flags, shutdown_countdown):
    global background_threads
    for idx, target_time in enumerate(target_times):
        stop_event = threading.Event()
        shutdown_enabled = bool(shutdown_flags[idx]) if idx < len(shutdown_flags) else False
        background_thread = threading.Thread(
            target=check_time_and_trigger,
            args=(audio, target_time, countdown_seconds, shutdown_enabled, shutdown_countdown, stop_event)
        )
        background_thread.daemon = True
        background_thread.start()
        background_threads.append((background_thread, stop_event))

def read_settings_from_ini(file_path='settings.ini'):
    config = configparser.ConfigParser()
    config.read(file_path)
    audio_file_path = config.get('Settings', 'audio_file_path')
    countdown_seconds = int(config.get('Settings', 'countdown_seconds', fallback='10'))
    shutdown_countdown_seconds = int(config.get('Settings', 'shutdown_countdown_seconds', fallback='60'))
    alarm_times_str = config.get('Settings', 'alarm_times', fallback='')
    shutdown_after_str = config.get('Settings', 'shutdown_after_alarm', fallback='')
    alarm_time_list = [x.strip() for x in alarm_times_str.split(',')] if alarm_times_str else []
    shutdown_after_list = [int(x.strip()) for x in shutdown_after_str.split(',')] if shutdown_after_str else []
    return audio_file_path, alarm_time_list, countdown_seconds, shutdown_after_list, shutdown_countdown_seconds

if __name__ == "__main__":
    # 初始化配置
    audio_path, alarm_times, countdown_seconds, shutdown_after_list, shutdown_countdown_seconds = read_settings_from_ini()
    audio_data = preload_audio(audio_path)
    
    # 创建应用实例
    app = App()
    app.alarm_shutdown_list = list(zip(alarm_times, shutdown_after_list))
    
    # 启动后台线程
    run_in_background(audio_data, alarm_times, countdown_seconds, shutdown_after_list, shutdown_countdown_seconds)
    
    # 启动主循环
    app.log_window.withdraw()
    app.log_window.mainloop()
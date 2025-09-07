import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import cv2
import numpy as np
import pyautogui
from PIL import Image, ImageTk, ImageGrab
import time
import win32gui
import win32ui
import win32con
import win32api
from ctypes import windll
import mss
import threading
import queue
import os
import json
from datetime import datetime


class AutoClickGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("自动点击工具 - GUI版本")
        self.root.geometry("1200x800")

        # 数据存储
        self.templates = []  # 存储模板信息
        self.target_windows = []  # 存储目标窗口句柄
        self.monitoring = False
        self.monitor_thread = None
        self.log_queue = queue.Queue()
        self.all_windows = []  # 存储所有窗口信息

        # 配置文件路径
        self.config_file = "auto_click_config.json"

        # 配置参数
        self.check_interval = tk.DoubleVar(value=1.0)
        self.match_threshold = tk.DoubleVar(value=0.8)
        self.log_level = tk.StringVar(value="info")
        # 每个窗口的点击类型（不持久化）：'拓展'(仅点击) 或 'cli'(点击并回车)
        self.window_click_type = {}

        # 加载配置
        self.load_config()

        # 初始化默认模板
        self.init_default_templates()

        self.setup_ui()
        self.refresh_windows()
        self.update_template_display()  # 显示已加载的模板
        self.process_log_queue()

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # 加载参数
                self.check_interval.set(config.get("check_interval", 1.0))
                self.match_threshold.set(config.get("match_threshold", 0.8))

                # 加载模板
                self.templates = config.get("templates", [])

                # 监控窗口不做持久化，不从配置恢复
                # self.target_windows = config.get('target_windows', [])
                # 点击类型不持久化，跳过恢复

                self.log("配置加载成功")
            else:
                self.log("未找到配置文件，使用默认设置")
                self.set_default_config()
        except Exception as e:
            self.log(f"配置加载失败: {e}")
            self.log("应用默认配置")
            self.set_default_config()
            # 自动保存默认配置
            self.save_config()

    def set_default_config(self):
        """设置默认配置"""
        self.check_interval.set(1.0)
        self.match_threshold.set(0.8)
        self.templates = []
        self.target_windows = []
        self.window_click_type = {}
        self.log("已应用默认配置")

    def save_config(self):
        """保存配置文件"""
        try:
            config = {
                "check_interval": self.check_interval.get(),
                "match_threshold": self.match_threshold.get(),
                "templates": self.templates,
            }

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            self.log("配置保存成功")
        except Exception as e:
            self.log(f"配置保存失败: {e}")

    def init_default_templates(self):
        """初始化默认模板"""
        default_templates = ["image1.png", "image2.png"]

        # 如果没有加载到模板，或者默认模板文件存在但不在列表中，则添加
        for template_file in default_templates:
            if os.path.exists(template_file):
                # 检查是否已在模板列表中
                exists = any(t["path"] == template_file for t in self.templates)
                if not exists:
                    try:
                        img = cv2.imread(template_file)
                        if img is not None:
                            height, width = img.shape[:2]
                            template_info = {
                                "name": template_file,
                                "path": template_file,
                                "size": f"{width}x{height}",
                            }
                            self.templates.append(template_info)
                            self.log(f"添加默认模板: {template_file}")
                    except Exception as e:
                        self.log(f"加载默认模板失败 {template_file}: {e}")
            else:
                self.log(f"默认模板文件不存在: {template_file}")

    def update_template_display(self):
        """更新模板列表显示"""
        # 清空现有显示
        for item in self.template_tree.get_children():
            self.template_tree.delete(item)

        # 添加所有模板到显示
        for template_info in self.templates:
            self.template_tree.insert(
                "",
                tk.END,
                values=(
                    template_info["name"],
                    template_info["path"],
                    template_info["size"],
                ),
            )

    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建上方内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 创建左侧面板
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 创建右侧面板
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 设置左侧面板
        self.setup_left_panel(left_frame)

        # 设置右侧面板
        self.setup_right_panel(right_frame)

        # 创建底部日志区域 - 占据整行
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 0))

        # 日志控制面板
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill=tk.X, pady=(0, 5))

        # 添加日志级别选择
        ttk.Label(log_control_frame, text="日志级别:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(
            log_control_frame, text="Info", variable=self.log_level, value="info"
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(
            log_control_frame, text="Debug", variable=self.log_level, value="debug"
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(log_control_frame, text="清除日志", command=self.clear_log).pack(
            side=tk.RIGHT, padx=(5, 0)
        )

        # 日志显示区域 - 设置固定高度
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=False)

        # 设置底部状态栏
        self.setup_status_bar()

    def setup_left_panel(self, parent):
        """设置左侧面板"""
        # 窗口选择区域
        window_frame = ttk.LabelFrame(
            parent, text="窗口列表 (双击选择/取消监控)", padding=10
        )
        window_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 窗口列表
        columns = ("hwnd", "title", "status", "type")
        self.window_tree = ttk.Treeview(
            window_frame, columns=columns, show="headings", height=20
        )
        self.window_tree.heading("hwnd", text="句柄")
        self.window_tree.heading("title", text="窗口标题")
        self.window_tree.heading("status", text="监控状态")
        self.window_tree.column("hwnd", width=80)
        self.window_tree.column("title", width=400)
        self.window_tree.column("status", width=80)
        self.window_tree.heading("type", text="Codex类型")
        self.window_tree.column("type", width=100)

        # 绑定双击事件
        self.window_tree.bind("<Double-1>", self.on_window_double_click)
        self.window_tree.bind("<Button-1>", self.on_window_tree_click)

        # 添加滚动条
        window_scrollbar = ttk.Scrollbar(
            window_frame, orient=tk.VERTICAL, command=self.window_tree.yview
        )
        self.window_tree.configure(yscrollcommand=window_scrollbar.set)

        self.window_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        window_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 窗口控制按钮
        window_btn_frame = ttk.Frame(parent)
        window_btn_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            window_btn_frame, text="刷新窗口列表", command=self.refresh_windows
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            window_btn_frame, text="全部取消监控", command=self.clear_all_monitoring
        ).pack(side=tk.LEFT)

    def setup_right_panel(self, parent):
        """设置右侧面板"""
        # 模板管理区域
        template_frame = ttk.LabelFrame(parent, text="模板管理", padding=10)
        template_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 模板列表
        template_list_frame = ttk.Frame(template_frame)
        template_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        columns = ("name", "path", "size")
        self.template_tree = ttk.Treeview(
            template_list_frame, columns=columns, show="headings", height=6
        )
        self.template_tree.heading("name", text="名称")
        self.template_tree.heading("path", text="路径")
        self.template_tree.heading("size", text="尺寸")
        self.template_tree.column("name", width=100)
        self.template_tree.column("path", width=200)
        self.template_tree.column("size", width=80)

        template_scrollbar = ttk.Scrollbar(
            template_list_frame, orient=tk.VERTICAL, command=self.template_tree.yview
        )
        self.template_tree.configure(yscrollcommand=template_scrollbar.set)

        self.template_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        template_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 模板控制按钮
        template_btn_frame = ttk.Frame(template_frame)
        template_btn_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(template_btn_frame, text="添加模板", command=self.add_template).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(
            template_btn_frame, text="删除模板", command=self.remove_template
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            template_btn_frame, text="预览模板", command=self.preview_template
        ).pack(side=tk.LEFT)

        # 参数配置区域
        config_frame = ttk.LabelFrame(parent, text="监控参数", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 5))

        # 检查间隔
        ttk.Label(config_frame, text="检查间隔(秒):").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )
        ttk.Scale(
            config_frame,
            from_=0.1,
            to=5.0,
            variable=self.check_interval,
            orient=tk.HORIZONTAL,
            length=200,
        ).grid(row=0, column=1, padx=(0, 5))
        ttk.Label(config_frame, textvariable=self.check_interval).grid(row=0, column=2)

        # 匹配阈值
        ttk.Label(config_frame, text="匹配阈值:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        ttk.Scale(
            config_frame,
            from_=0.1,
            to=1.0,
            variable=self.match_threshold,
            orient=tk.HORIZONTAL,
            length=200,
            command=lambda v: self.match_threshold.set(round(float(v), 2)),
        ).grid(row=1, column=1, padx=(0, 5), pady=(5, 0))
        threshold_label = ttk.Label(config_frame, text="0.80")
        threshold_label.grid(row=1, column=2, pady=(5, 0))

        # 绑定阈值变化事件来更新显示
        def update_threshold_label(*args):
            threshold_label.config(text=f"{self.match_threshold.get():.2f}")

        self.match_threshold.trace("w", update_threshold_label)

        # 控制按钮区域
        control_frame = ttk.LabelFrame(parent, text="监控控制", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 5))

        self.start_btn = ttk.Button(
            control_frame, text="开始监控", command=self.start_monitoring
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = ttk.Button(
            control_frame,
            text="停止监控",
            command=self.stop_monitoring,
            state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(control_frame, text="保存配置", command=self.save_config).pack(
            side=tk.LEFT
        )

    def setup_status_bar(self):
        """设置状态栏"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(self.status_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

        self.monitor_status_label = ttk.Label(
            self.status_frame, text="未监控", foreground="red"
        )
        self.monitor_status_label.pack(side=tk.RIGHT, padx=10, pady=5)

    def log(self, message, level="info"):
        """添加日志消息"""
        # 检查是否应该显示此级别的消息
        current_level = self.log_level.get()
        if level == "debug" and current_level == "info":
            return  # info模式不显示debug消息

        timestamp = datetime.now().strftime("%H:%M:%S")
        level_prefix = "[DEBUG]" if level == "debug" else "[INFO]"
        self.log_queue.put(f"[{timestamp}] {level_prefix} {message}")

    def debug_log(self, message):
        """添加调试日志"""
        self.log(message, "debug")

    def info_log(self, message):
        """添加信息日志"""
        self.log(message, "info")

    def process_log_queue(self):
        """处理日志队列"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_log_queue)

    def refresh_windows(self):
        """刷新窗口列表"""
        # 清空当前列表
        for item in self.window_tree.get_children():
            self.window_tree.delete(item)

        # 获取所有窗口
        self.all_windows = self.list_visible_windows()

        # 分类：监控中的窗口 与 其他窗口
        monitored_windows = []
        other_windows = []

        for hwnd, title in self.all_windows:
            if hwnd in self.target_windows:
                monitored_windows.append((hwnd, title))
            else:
                other_windows.append((hwnd, title))

        # 先插入监控中的窗口
        # 先插入监控中的窗口
        for hwnd, title in monitored_windows:
            self.window_tree.insert(
                "", tk.END, values=(hwnd, title, "? 监控中", self.window_click_type.get(hwnd, "拓展")), tags=("monitoring",)
            )

        # 再插入其他窗口
        for hwnd, title in other_windows:
            self.window_tree.insert(
                "", tk.END, values=(hwnd, title, "", self.window_click_type.get(hwnd, "拓展")), tags=("normal",)
            )
        self.log(f"刷新窗口列表，找到 {len(self.all_windows)} 个窗口，其中 {len(monitored_windows)} 个在监控")
    def on_window_double_click(self, event):
        """窗口列表双击事件"""
        selection = self.window_tree.selection()
        if not selection:
            return

        item = self.window_tree.item(selection[0])
        values = item["values"]
        # 兼容三列/四列
        if len(values) >= 4:
            hwnd, title, status, current_type = values
        else:
            hwnd, title, status = values
            current_type = self.window_click_type.get(int(hwnd), "拓展")
        hwnd = int(hwnd)

        if hwnd in self.target_windows:
            # 取消监控
            self.target_windows.remove(hwnd)
            self.window_tree.item(
                selection[0], values=(hwnd, title, "", self.window_click_type.get(hwnd, "拓展")), tags=("normal",)
            )
            self.log(f"取消监控窗口: {title}")

            # 自动保存配置（不包含窗口与点击类型）
            self.save_config()
        else:
            # 添加监控
            self.target_windows.append(hwnd)
            # 默认点击类型：拓展（仅点击）
            self.window_click_type[hwnd] = self.window_click_type.get(hwnd, "拓展")
            self.window_tree.item(
                selection[0], values=(hwnd, title, "✅ 监控中", self.window_click_type[hwnd]), tags=("monitoring",)
            )
            self.log(f"添加监控窗口: {title}")

            # 自动保存配置（不包含窗口与点击类型）
            self.save_config()

        # 重新排序，将监控在前面
        self.sort_windows()
    def sort_windows(self):
        """排序窗口，监控的在前面"""
        # 获取所有项目
        all_items = []
        for item in self.window_tree.get_children():
            values = self.window_tree.item(item)["values"]
            tags = self.window_tree.item(item)["tags"]
            all_items.append((values, tags))

        # 清空列表
        for item in self.window_tree.get_children():
            self.window_tree.delete(item)

        # 排序：监控的在前面
        all_items.sort(key=lambda x: (0 if x[0][2] == "✓ 监控中" else 1, x[0][1]))

        # 重新插入
        for values, tags in all_items:
            self.window_tree.insert("", tk.END, values=values, tags=tags)

    def on_window_tree_click(self, event):
        """点击窗口列表，若点击到type列，弹出下拉选择类型"""
        try:
            region = self.window_tree.identify_region(event.x, event.y)
            if region != 'cell':
                return
            column_id = self.window_tree.identify_column(event.x)  # like '#4'
            row_id = self.window_tree.identify_row(event.y)
            if not row_id:
                return
            # 解析列名
            try:
                col_index = int(column_id.replace('#', '')) - 1
            except Exception:
                return
            columns = self.window_tree['columns']
            if col_index < 0 or col_index >= len(columns):
                return
            col_name = columns[col_index]
            if col_name != 'type':
                return
            # 定位单元格
            bbox = self.window_tree.bbox(row_id, column_id)
            if not bbox:
                return
            x, y, w, h = bbox
            # 当前值
            current = self.window_tree.set(row_id, 'type') or '拓展'
            # 销毁旧编辑器
            if hasattr(self, '_type_editor') and self._type_editor is not None:
                try:
                    self._type_editor.destroy()
                except Exception:
                    pass
                self._type_editor = None
            # 创建下拉
            cb = ttk.Combobox(self.window_tree, values=['拓展', 'cli'], state='readonly')
            cb.set(current if current in ['拓展', 'cli'] else '拓展')
            cb.place(x=x, y=y, width=w, height=h)

            def commit(event=None):
                val = cb.get() or '拓展'
                self.window_tree.set(row_id, 'type', val)
                # 更新映射
                try:
                    hwnd_str = self.window_tree.set(row_id, 'hwnd')
                    if hwnd_str:
                        self.window_click_type[int(hwnd_str)] = val
                except Exception:
                    pass
                cb.destroy()
                self._type_editor = None

            cb.bind('<<ComboboxSelected>>', commit)
            cb.bind('<FocusOut>', commit)
            cb.focus_set()
            self._type_editor = cb
        except Exception:
            pass

    def clear_all_monitoring(self):
        """清除所有监控"""
        if not self.target_windows:
            messagebox.showinfo("提示", "当前没有监控任何窗口")
            return

        result = messagebox.askyesno(
            "确认", f"确定要取消监控所有 {len(self.target_windows)} 个窗口吗？"
        )
        if result:
            self.target_windows.clear()
            self.refresh_windows()
            self.log("已取消所有窗口的监控")

            # 自动保存配置
            self.save_config()

    def list_visible_windows(self):
        """列出所有可见窗口"""

        def enum_windows_proc(hwnd, result_list):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if window_title:
                    result_list.append((hwnd, window_title))
            return True

        windows = []
        win32gui.EnumWindows(enum_windows_proc, windows)
        return windows

    def add_template(self):
        """添加模板（支持多选）"""
        file_paths = filedialog.askopenfilenames(
            title="选择模板图像（可多选）",
            filetypes=[("图像文件", "*.png *.jpg *.jpeg *.bmp *.gif")],
        )

        if not file_paths:
            return

        added_count = 0

        for file_path in file_paths:
            try:
                # 加载图像获取尺寸
                img = cv2.imread(file_path)
                if img is None:
                    self.log(f"无法加载图像文件: {file_path}")
                    continue

                height, width = img.shape[:2]
                name = os.path.basename(file_path)

                # 检查是否已存在
                exists = any(t["path"] == file_path for t in self.templates)
                if exists:
                    self.log(f"模板已存在，跳过: {name}")
                    continue

                # 添加到模板列表
                template_info = {
                    "name": name,
                    "path": file_path,
                    "size": f"{width}x{height}",
                }

                self.templates.append(template_info)
                self.template_tree.insert(
                    "", tk.END, values=(name, file_path, f"{width}x{height}")
                )
                self.log(f"添加模板: {name}")
                added_count += 1

            except Exception as e:
                self.log(f"添加模板失败 {file_path}: {e}")

        if added_count > 0:
            self.log(f"成功添加 {added_count} 个模板")
            # 自动保存配置
            self.save_config()
        else:
            messagebox.showinfo("提示", "没有新的模板被添加")

    def remove_template(self):
        """删除模板"""
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的模板")
            return

        index = self.template_tree.index(selection[0])
        template_info = self.templates[index]

        del self.templates[index]
        self.template_tree.delete(selection[0])
        self.log(f"删除模板: {template_info['name']}")

        # 自动保存配置
        self.save_config()

    def preview_template(self):
        """预览模板"""
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要预览的模板")
            return

        index = self.template_tree.index(selection[0])
        template_info = self.templates[index]

        try:
            # 创建预览窗口
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"预览: {template_info['name']}")

            # 加载和显示图像
            img = Image.open(template_info["path"])

            # 如果图像太大，缩放显示
            max_size = (400, 400)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            label = tk.Label(preview_window, image=photo)
            label.image = photo  # 保持引用
            label.pack(padx=10, pady=10)

        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {e}")

    def start_monitoring(self):
        """开始监控"""
        if not self.target_windows:
            messagebox.showwarning("警告", "请先添加要监控的窗口")
            return

        if not self.templates:
            messagebox.showwarning("警告", "请先添加模板图像")
            return

        self.monitoring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.monitor_status_label.config(text="监控中", foreground="green")

        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.log("开始监控")

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.monitor_status_label.config(text="已停止", foreground="red")

        self.log("停止监控")

    def monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                for hwnd in list(self.target_windows):
                    if not self.monitoring:
                        break
                    try:
                        window_title = win32gui.GetWindowText(hwnd)
                    except:
                        continue
                    screen = self.capture_window(hwnd)
                    if screen is None:
                        self.debug_log(f"窗口截图失败: {window_title}")
                        continue
                    self.debug_log(f"成功获取画面: {window_title}, 大小: {screen.shape}")
                    for template_info in self.templates:
                        if not self.monitoring:
                            break
                        found, x, y = self.find_template(screen, template_info["path"], self.match_threshold.get())
                        if found:
                            self.log(f"在窗口 '{window_title}' 找到模板 '{template_info['name']}'")
                            self.bring_window_to_front(hwnd)
                            rect = win32gui.GetWindowRect(hwnd)
                            screen_x = rect[0] + x
                            screen_y = rect[1] + y
                            pyautogui.moveTo(screen_x, screen_y)
                            pyautogui.click()
                            if self.window_click_type.get(hwnd, "拓展") == "cli":
                                time.sleep(0.05)
                                pyautogui.press("enter")
                                self.debug_log("已在点击后发送回车")
                            self.log(f"点击位置: ({screen_x}, {screen_y})")
                            time.sleep(1)
                            break
                        else:
                            self.debug_log(f"模板 '{template_info['name']}' 未匹配")
                time.sleep(self.check_interval.get())
            except Exception as e:
                self.log(f"监控异常: {e}")
    def capture_window(self, hwnd):
        """截取窗口（基础PrintWindow方法）"""
        try:
            windll.user32.SetProcessDPIAware()

            # 获取窗口尺寸
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x1, y1 = rect
            width = x1 - x
            height = y1 - y

            if width <= 0 or height <= 0:
                return None

            # 执行截图
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)

            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

            if result:
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)
                img = Image.frombuffer(
                    "RGB",
                    (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
                    bmpstr,
                    "raw",
                    "BGRX",
                    0,
                    1,
                )
                img_np = np.array(img)
                img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            else:
                img_bgr = None

            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)

            return img_bgr

        except Exception as e:
            self.log(f"截图失败: {e}")
            return None

    def find_template(self, screen, template_path, threshold):
        """查找模板"""
        try:
            template = cv2.imread(template_path)
            if template is None:
                return False, 0, 0

            screen_h, screen_w = screen.shape[:2]
            template_h, template_w = template.shape[:2]

            if template_h > screen_h or template_w > screen_w:
                return False, 0, 0

            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= threshold:
                center_x = max_loc[0] + template_w // 2
                center_y = max_loc[1] + template_h // 2
                return True, center_x, center_y

            return False, 0, 0

        except Exception as e:
            self.log(f"模板匹配错误: {e}")
            return False, 0, 0

    def bring_window_to_front(self, hwnd):
        """将窗口切换到前台"""
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetActiveWindow(hwnd)
            time.sleep(0.2)
        except Exception as e:
            self.log(f"切换窗口失败: {e}")

    def clear_log(self):
        """清除日志"""
        self.log_text.delete(1.0, tk.END)

    def on_closing(self):
        """关闭程序时的处理"""
        if self.monitoring:
            self.stop_monitoring()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = AutoClickGUI(root)

    # 设置关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # 启动GUI
    root.mainloop()


if __name__ == "__main__":
    main()

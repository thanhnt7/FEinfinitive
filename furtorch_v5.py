# furtorch_v5.py
# FIXED: Updated to parse new text-based log format (ItemChange/BagMgr)

import tkinter as tk
from tkinter import ttk, messagebox
import json
import time
import re
import os
from datetime import datetime
import threading

try:
    import win32gui
    import win32process
    import psutil
    HAS_WIN_SUPPORT = True
except ImportError:
    HAS_WIN_SUPPORT = False
    print("⚠ Windows modules not available")

# ==================== ORIGINAL PARSER ====================

def convert_from_log_structure(log_text):
    lines = [line.strip() for line in log_text.split('\n') if line.strip()]
    stack = []
    root = {}

    for line in lines:
        level = line.count('|')
        content = re.sub(r'\|+', '', line).strip()

        while len(stack) > level:
            stack.pop()

        if not stack:
            parent = root
        else:
            parent = stack[-1]

        if parent is None:
            continue

        if '[' in content and ']' in content:
            key_part = content[:content.index('[')].strip()
            value_part = content[content.index('[') + 1: content.rindex(']')].strip()

            if value_part.lower() == 'true':
                value = True
            elif value_part.lower() == 'false':
                value = False
            elif re.match(r'^-?\d+$', value_part):
                value = int(value_part)
            else:
                value = value_part

            keys = [k.strip() for k in key_part.split('+') if k.strip()]
            current_node = parent

            for i in range(len(keys)):
                key = keys[i]
                if not key or current_node is None:
                    continue

                if i == len(keys) - 1:
                    current_node[key] = value
                else:
                    if not isinstance(current_node, dict):
                        break
                    if key not in current_node:
                        current_node[key] = {}
                    current_node = current_node[key]
                    if current_node is None:
                        break

            stack.append(current_node)
        else:
            key_part = content.strip()
            keys = [k.strip() for k in key_part.split('+') if k.strip()]
            current_node = parent

            for key in keys:
                if not key or current_node is None:
                    continue
                if not isinstance(current_node, dict):
                    break
                if key not in current_node:
                    current_node[key] = {}
                current_node = current_node[key]
                if current_node is None:
                    break

            stack.append(current_node)

    return root


def scan_log_for_pickups(log_text):
    """
    NEW: Scan for ItemChange and BagMgr events in the new log format.

    Example format:
    ItemChange@ ProtoName=PickItems start
    ItemChange@ Update Id=100200_... BagNum=464 in PageId=102 SlotId=22
    BagMgr@:Modfy BagItem PageId = 102 SlotId = 22 ConfigBaseId = 100200 Num = 464
    ItemChange@ ProtoName=PickItems end
    """
    drops_found = []
    lines = log_text.split('\n')

    for line in lines:
        # Look for BagMgr modify events with ConfigBaseId and Num
        if 'BagMgr@' in line and 'ConfigBaseId' in line and 'Num = ' in line:
            try:
                # Extract ConfigBaseId (item ID)
                base_id_match = re.search(r'ConfigBaseId\s*=\s*(\d+)', line)
                # Extract Num (count) - need to be careful to get the right Num
                num_match = re.search(r'Num\s*=\s*(\d+)', line)

                if base_id_match and num_match:
                    item_id = base_id_match.group(1)
                    # For Num, we want the DIFFERENCE from previous count
                    # But since we don't track previous, we'll just use increment of 1
                    # This might need adjustment based on actual behavior
                    drops_found.append((item_id, 1))
            except Exception as e:
                print(f"[ERROR] Failed to parse BagMgr line: {e}")

        # Alternative: Look for ItemChange Update events
        elif 'ItemChange@' in line and 'Update' in line and 'BagNum=' in line:
            try:
                # Extract the item ID from the UUID-like string
                # Format: Id=100200_c26bfde9-af0d-11f0-b8b8-00000000002a
                id_match = re.search(r'Id=(\d+)_', line)
                if id_match:
                    item_id = id_match.group(1)
                    # Count as 1 pickup (we don't have delta info)
                    # Note: This will be deduplicated with BagMgr events
                    # So we'll prefer BagMgr events and skip ItemChange
                    pass
            except Exception as e:
                print(f"[ERROR] Failed to parse ItemChange line: {e}")

    return drops_found


def parse_pickup_events(log_text):
    """
    Parse pickup events from new log format.
    Returns list of (item_id, count) tuples.
    """
    return scan_log_for_pickups(log_text)


class FurTorchV5:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("FurTorch v5.0 - New Log Format")
        self.window.geometry("600x450")
        self.window.resizable(False, False)

        # State
        self.is_tracking = False
        self.is_in_map = False
        self.current_time = 0
        self.total_time = 0
        self.current_income = 0
        self.total_income = 0
        self.map_count = 0
        self.drops_current = {}
        self.drops_total = {}
        self.view_mode = "current"
        self.start_time = time.time()

        # Map cost tracking
        self.current_map_cost = 0.0  # Auto-calculated from consumed items
        self.total_map_cost = 0.0  # Cumulative map cost across all maps
        self.consumed_items_current = {}  # Track consumed items per map

        # Track previous bag counts to calculate deltas
        self.previous_bag_counts = {}
        
        # Settings
        self.settings = {
            "map_cost": 0.0,
            "opacity": 1.0,
            "apply_tax": False,
            "log_path": ""
        }
        
        # Load data
        self.load_item_database()
        self.load_settings()
        
        # Create UI
        self.create_ui()
        
        # Find game
        if HAS_WIN_SUPPORT:
            self.find_game_log()
        else:
            self.status.config(text="⚠ Windows support not available", foreground='orange')
        
        # Start threads
        self.running = True
        self.log_position = 0
        self.start_threads()
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_item_database(self):
        self.item_db = {}
        try:
            with open("full_table_en.json", "r", encoding="utf-8") as f:
                full_table = json.load(f)
            for item_id, data in full_table.items():
                self.item_db[item_id] = {
                    "name": data.get("name", "Unknown"),
                    "type": data.get("type", "Other"),
                    "price": data.get("price", 0)
                }
            print(f"✓ Loaded {len(self.item_db)} items from database")
        except Exception as e:
            print(f"⚠ Error loading database: {e}")
            self.item_db = {
                "100300": {"name": "初火源质", "type": "硬通货", "price": 1.0},
                "100200": {"name": "初火灵砂", "type": "硬通货", "price": 0.002},
                "5028": {"name": "异界回响", "type": "硬通货", "price": 0.14},
            }
            
    def create_ui(self):
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', self.settings['opacity'])
        
        main = ttk.Frame(self.window, padding="10")
        main.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main, text="🔥 FurTorch v5 (New Format)",
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=3, pady=5)
        
        stats = ttk.LabelFrame(main, text="Statistics", padding="10")
        stats.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(stats, text="Current:").grid(row=0, column=0, sticky=tk.W)
        self.lbl_time = ttk.Label(stats, text="0m00s", font=('Arial', 10, 'bold'))
        self.lbl_time.grid(row=0, column=1, padx=5)
        self.lbl_speed = ttk.Label(stats, text="0/min")
        self.lbl_speed.grid(row=0, column=2)
        
        ttk.Label(stats, text="Total:").grid(row=1, column=0, sticky=tk.W)
        self.lbl_total_time = ttk.Label(stats, text="0m00s", font=('Arial', 10, 'bold'))
        self.lbl_total_time.grid(row=1, column=1, padx=5)
        self.lbl_total_speed = ttk.Label(stats, text="0/min")
        self.lbl_total_speed.grid(row=1, column=2)
        
        income_frame = ttk.Frame(main)
        income_frame.grid(row=2, column=0, columnspan=3, pady=10)

        # Map cost display (above profit)
        self.lbl_map_cost = ttk.Label(income_frame, text="💰 Cost: 0.00",
                                      font=('Arial', 10), foreground='#ef4444')
        self.lbl_map_cost.grid(row=0, column=0, columnspan=2, pady=(0, 5))

        # Profit display
        self.lbl_income = ttk.Label(income_frame, text="🔥 Profit: 0.00",
                                    font=('Arial', 20, 'bold'), foreground='#10b981')
        self.lbl_income.grid(row=1, column=0, padx=15)

        self.lbl_maps = ttk.Label(income_frame, text="🎫 0", font=('Arial', 12))
        self.lbl_maps.grid(row=1, column=1, padx=15)
        
        btn = ttk.Frame(main)
        btn.grid(row=3, column=0, columnspan=3, pady=5)
        
        self.btn_start = ttk.Button(btn, text="▶ Start", command=self.manual_start, width=10)
        self.btn_start.grid(row=0, column=0, padx=2)
        
        self.btn_end = ttk.Button(btn, text="⏹ End", command=self.manual_end, 
                                  state=tk.DISABLED, width=10)
        self.btn_end.grid(row=0, column=1, padx=2)
        
        self.btn_view = ttk.Button(btn, text="Total", command=self.toggle_view, width=10)
        self.btn_view.grid(row=0, column=2, padx=2)
        
        extra = ttk.Frame(main)
        extra.grid(row=4, column=0, columnspan=3, pady=5)
        
        ttk.Button(extra, text="Drops", command=self.show_drops, width=8).grid(row=0, column=0, padx=2)
        ttk.Button(extra, text="Settings", command=self.show_settings, width=8).grid(row=0, column=1, padx=2)
        ttk.Button(extra, text="Export", command=self.export_data, width=8).grid(row=0, column=2, padx=2)
        ttk.Button(extra, text="Reset", command=self.reset_all, width=8).grid(row=0, column=3, padx=2)
        
        self.status = ttk.Label(main, text="Initializing...", foreground='gray', font=('Arial', 9))
        self.status.grid(row=5, column=0, columnspan=3, pady=10)
        
    def find_game_log(self):
        try:
            hwnd = win32gui.FindWindow(None, "Torchlight: Infinite  ")
            if not hwnd:
                self.status.config(text="⚠ Game not detected. Start game first!", foreground='orange')
                return
            
            tid, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            game_exe = process.exe()
            
            print(f"Game exe: {game_exe}")
            
            game_dir = os.path.dirname(game_exe)
            
            # Try correct path with UE_game
            log_path1 = os.path.join(game_dir, "../../UE_game/TorchLight/Saved/Logs/UE_game.log")
            log_path1 = os.path.normpath(log_path1)
            
            # Fallback path
            log_path2 = os.path.join(game_dir, "../../TorchLight/Saved/Logs/UE_game.log")
            log_path2 = os.path.normpath(log_path2)
            
            log_path = None
            if os.path.exists(log_path1):
                log_path = log_path1
                print(f"✓ Found log (Method 1): {log_path}")
            elif os.path.exists(log_path2):
                log_path = log_path2
                print(f"✓ Found log (Method 2): {log_path}")
            else:
                print(f"❌ Log not found")
                self.status.config(text="⚠ Log file not found! Enable logging!", 
                                  foreground='orange')
                return
            
            self.settings['log_path'] = log_path

            # Move to end of file to skip historical data - only track current session
            print("Moving to end of log file (skipping historical data)...")
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Seek to end of file immediately - don't read historical data
                f.seek(0, 2)
                self.log_position = f.tell()

            print(f"✓ Ready to track current session only (historical data ignored)")
            self.status.config(text="✓ Game detected! Monitoring pickup events!",
                              foreground='#10b981')
            print(f"✓ Monitoring: {log_path}")
            print("✓ Looking for: ItemChange and BagMgr pickup events")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            self.status.config(text=f"⚠ Error: {str(e)[:40]}", foreground='red')
            
    def start_threads(self):
        def update_loop():
            while self.running:
                if self.is_tracking:
                    self.window.after(0, self.update_display)
                time.sleep(1)
        threading.Thread(target=update_loop, daemon=True).start()
        
        if self.settings.get('log_path'):
            def monitor_loop():
                while self.running:
                    try:
                        self.read_new_log_lines()
                    except Exception as e:
                        print(f"Monitor error: {e}")
                    time.sleep(0.5)
            threading.Thread(target=monitor_loop, daemon=True).start()
            print("✓ Log monitor thread started")
            
    def read_new_log_lines(self):
        if not self.settings.get('log_path'):
            return
            
        try:
            with open(self.settings['log_path'], 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.log_position)
                new_text = f.read()
                self.log_position = f.tell()
                
                if new_text:
                    self.parse_log_text(new_text)
        except Exception as e:
            print(f"[ERROR] Read error: {e}")
            
    def parse_log_text(self, text):
        # Check map transitions
        if "PageApplyBase@ _UpdateGameEnd" in text:
            if "XZ_YuJinZhiXiBiNanSuo200" in text and "NextSceneName = World'/Game/Art/Maps" in text:
                if not self.is_in_map:
                    print("[MAP] Entering map")
                    self.window.after(0, self.auto_start_map)
            elif "NextSceneName = World'/Game/Art/Maps/01SD/XZ_YuJinZhiXiBiNanSuo200" in text:
                if self.is_in_map:
                    print("[MAP] Exiting map")
                    self.window.after(0, self.auto_end_map)
        
        # NEW: Look for ItemChange/BagMgr pickup events and calculate deltas
        lines = text.split('\n')
        for line in lines:
            if 'BagMgr@' in line and 'ConfigBaseId' in line and 'Num = ' in line:
                try:
                    # Extract ConfigBaseId (item ID)
                    base_id_match = re.search(r'ConfigBaseId\s*=\s*(\d+)', line)
                    # Extract Num (total count in bag)
                    num_match = re.search(r'Num\s*=\s*(\d+)', line)

                    if base_id_match and num_match:
                        item_id = base_id_match.group(1)
                        new_count = int(num_match.group(1))

                        # Calculate delta from previous count
                        old_count = self.previous_bag_counts.get(item_id, 0)
                        delta = new_count - old_count

                        if delta > 0:
                            # Items picked up
                            print(f"[DROP] ID:{item_id} x{delta} (bag: {old_count} -> {new_count})")
                            self.window.after(0, lambda id=item_id, c=delta: self.add_drop(id, c))
                        elif delta < 0:
                            # Items consumed (negative delta)
                            consumed = abs(delta)
                            print(f"[CONSUMED] ID:{item_id} x{consumed} (bag: {old_count} -> {new_count})")
                            self.window.after(0, lambda id=item_id, c=consumed: self.add_consumed(id, c))

                        # Update tracking
                        self.previous_bag_counts[item_id] = new_count
                except Exception as e:
                    print(f"[ERROR] Failed to parse BagMgr line: {e}")
                
    def add_consumed(self, item_id, count):
        """Track consumed items and calculate map cost"""
        if item_id not in self.item_db:
            print(f"⚠ Unknown consumed item: {item_id}")
            return

        item = self.item_db[item_id]
        price = item['price']

        if self.settings['apply_tax'] and item_id != "100300":
            price = price * 0.875

        value = price * count

        # Track consumed items for current map
        self.consumed_items_current[item_id] = self.consumed_items_current.get(item_id, 0) + count

        # Add to map cost
        self.current_map_cost += value

        print(f"✓ Consumed: {item['name']} x{count} = {value:.2f} (total map cost: {self.current_map_cost:.2f})")
        self.update_display()

    def auto_start_map(self):
        if not self.is_in_map:
            self.is_in_map = True
            self.is_tracking = True
            self.current_time = 0
            self.current_income = 0  # Don't subtract manual map_cost anymore
            self.drops_current = {}
            self.consumed_items_current = {}
            self.current_map_cost = 0.0  # Reset auto-calculated map cost
            self.map_count += 1
            self.start_time = time.time()
            self.btn_start.config(state=tk.DISABLED)
            self.btn_end.config(state=tk.NORMAL)
            self.status.config(text=f"🗺 Tracking Map #{self.map_count}...", foreground='#10b981')
            
    def auto_end_map(self):
        if self.is_in_map:
            self.is_in_map = False
            self.is_tracking = False
            elapsed = int(time.time() - self.start_time)
            self.total_time += elapsed

            # Subtract map cost from total income (so total profit is net)
            self.total_income -= self.current_map_cost

            # Accumulate total map cost across all maps
            self.total_map_cost += self.current_map_cost

            # Calculate net profit for this map
            net_profit = self.current_income - self.current_map_cost

            self.btn_start.config(state=tk.NORMAL)
            self.btn_end.config(state=tk.DISABLED)
            self.status.config(text=f"✓ Map done! Profit: {net_profit:.2f} (cost: {self.current_map_cost:.2f})",
                              foreground='#8b5cf6')
            
    def manual_start(self):
        self.auto_start_map()
        
    def manual_end(self):
        self.auto_end_map()
        
    def add_drop(self, item_id, count):
        if item_id not in self.item_db:
            print(f"⚠ Unknown item: {item_id}")
            return
        
        item = self.item_db[item_id]
        price = item['price']
        
        if self.settings['apply_tax'] and item_id != "100300":
            price = price * 0.875
        
        value = price * count
        
        self.drops_current[item_id] = self.drops_current.get(item_id, 0) + count
        self.drops_total[item_id] = self.drops_total.get(item_id, 0) + count
        
        self.current_income += value
        self.total_income += value
        
        # Write to drop_log.txt
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open("drop_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {item['name']} x{count} ({price:.3f})\n")
            print(f"✓ Logged to drop_log.txt")
        except Exception as e:
            print(f"⚠ Could not write to drop_log.txt: {e}")
        
        print(f"✓ Added: {item['name']} x{count} = {value:.2f}")
        self.update_display()
        
    def update_display(self):
        if self.is_tracking:
            self.current_time = int(time.time() - self.start_time)

        m, s = divmod(self.current_time, 60)
        self.lbl_time.config(text=f"{m}m{s:02d}s")

        tm, ts = divmod(self.total_time + (self.current_time if self.is_tracking else 0), 60)
        self.lbl_total_time.config(text=f"{tm}m{ts:02d}s")

        # Calculate net profit (income - map cost)
        current_net_profit = self.current_income - self.current_map_cost
        total_net_profit = self.total_income  # Total already accounts for all maps

        if self.current_time > 0:
            speed = (current_net_profit / self.current_time) * 60
            self.lbl_speed.config(text=f"{speed:.2f}/min")

        total_time_calc = self.total_time + (self.current_time if self.is_tracking else 0)
        if total_time_calc > 0:
            total_speed = (total_net_profit / total_time_calc) * 60
            self.lbl_total_speed.config(text=f"{total_speed:.2f}/min")

        # Display map cost
        if self.view_mode == "current":
            self.lbl_map_cost.config(text=f"💰 Cost: {self.current_map_cost:.2f}")
        else:
            self.lbl_map_cost.config(text=f"💰 Total Cost: {self.total_map_cost:.2f}")

        # Display net profit
        profit = current_net_profit if self.view_mode == "current" else total_net_profit
        color = '#10b981' if profit >= 0 else '#ef4444'
        self.lbl_income.config(text=f"🔥 Profit: {profit:.2f}", foreground=color)
        self.lbl_maps.config(text=f"🎫 {self.map_count}")
        
    def toggle_view(self):
        self.view_mode = "total" if self.view_mode == "current" else "current"
        self.btn_view.config(text="Current" if self.view_mode == "total" else "Total")
        self.update_display()
        
    def show_drops(self):
        win = tk.Toplevel(self.window)
        win.title("Drop List")
        win.geometry("500x400")
        win.attributes('-topmost', True)
        
        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=('Consolas', 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        drops = self.drops_current if self.view_mode == "current" else self.drops_total
        
        if not drops:
            listbox.insert(tk.END, "No drops yet!")
        else:
            for item_id, count in sorted(drops.items(), 
                                        key=lambda x: self.item_db[x[0]]['price'] * x[1], 
                                        reverse=True):
                item = self.item_db[item_id]
                price = item['price']
                if self.settings['apply_tax'] and item_id != "100300":
                    price *= 0.875
                value = price * count
                listbox.insert(tk.END, f"{item['name']} x{count} [{value:.2f}]")
            
    def show_settings(self):
        win = tk.Toplevel(self.window)
        win.title("Settings")
        win.geometry("350x200")
        win.attributes('-topmost', True)
        
        frame = ttk.Frame(win, padding="20")
        frame.pack()
        
        ttk.Label(frame, text="Map Cost:").grid(row=0, column=0, pady=5, sticky=tk.W)
        cost_var = tk.StringVar(value=str(self.settings['map_cost']))
        ttk.Entry(frame, textvariable=cost_var, width=15).grid(row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Opacity:").grid(row=1, column=0, pady=5, sticky=tk.W)
        opacity_var = tk.DoubleVar(value=self.settings['opacity'])
        ttk.Scale(frame, from_=0.1, to=1.0, variable=opacity_var, 
                 command=lambda v: self.window.attributes('-alpha', float(v))).grid(row=1, column=1, pady=5)
        
        tax_var = tk.BooleanVar(value=self.settings['apply_tax'])
        ttk.Checkbutton(frame, text="Apply Tax (12.5%)", variable=tax_var).grid(row=2, columnspan=2, pady=5)
        
        def save():
            try:
                self.settings['map_cost'] = float(cost_var.get())
                self.settings['opacity'] = opacity_var.get()
                self.settings['apply_tax'] = tax_var.get()
                self.save_settings()
                messagebox.showinfo("Settings", "Saved!")
                win.destroy()
            except:
                messagebox.showerror("Error", "Invalid map cost!")
        
        ttk.Button(frame, text="Save", command=save).grid(row=3, columnspan=2, pady=10)
        
    def export_data(self):
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = {
            "total_time": self.total_time,
            "total_income": self.total_income,
            "total_map_cost": self.total_map_cost,
            "map_count": self.map_count,
            "drops": {self.item_db[k]['name']: v for k, v in self.drops_total.items()}
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Export", f"Saved to {filename}")
        
    def reset_all(self):
        if messagebox.askyesno("Reset", "Reset all statistics?"):
            self.current_time = self.total_time = 0
            self.current_income = self.total_income = 0
            self.current_map_cost = self.total_map_cost = 0.0
            self.map_count = 0
            self.drops_current = self.drops_total = {}
            self.consumed_items_current = {}
            self.is_tracking = self.is_in_map = False
            self.btn_start.config(state=tk.NORMAL)
            self.btn_end.config(state=tk.DISABLED)
            self.update_display()
            self.status.config(text="✓ Statistics reset", foreground='gray')
            
    def load_settings(self):
        try:
            if os.path.exists("config.json"):
                with open("config.json", 'r', encoding='utf-8') as f:
                    self.settings.update(json.load(f))
        except:
            pass
            
    def save_settings(self):
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except:
            pass
            
    def on_closing(self):
        self.running = False
        self.save_settings()
        self.window.destroy()
        
    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    print("="*60)
    print("FurTorch v5.0 - New Log Format Parser")
    print("="*60)
    print("Updated: Now parses ItemChange/BagMgr pickup events")
    print("Compatible with: 2025.10.23+ game log format")
    print()
    
    try:
        app = FurTorchV5()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

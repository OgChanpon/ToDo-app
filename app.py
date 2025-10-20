import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, timedelta
import platform # OSを判別するためにインポート

# --- NEW: OSに応じて最適な日本語フォントを選択 ---
def get_font():
    os_name = platform.system()
    if os_name == "Windows":
        return ("Yu Gothic UI", 10)
    elif os_name == "Darwin": # macOS
        return ("Hiragino Sans", 11)
    else: # Linuxなど
        # WSLにインストールしたフォントを指定
        return ("Noto Sans CJK JP", 10)

DEFAULT_FONT = get_font()
DEFAULT_FONT_BOLD = (DEFAULT_FONT[0], DEFAULT_FONT[1], 'bold')


# --- データ管理 ---
FILENAME = "tasks.json"
tasks = []

def load_tasks():
    global tasks
    if os.path.exists(FILENAME):
        try:
            with open(FILENAME, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except json.JSONDecodeError:
            tasks = []
    else:
        tasks = []

def save_tasks():
    with open(FILENAME, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def cleanup_old_completed_tasks():
    global tasks
    today = datetime.now()
    start_of_this_week = today - timedelta(days=today.weekday())

    tasks_to_keep = []
    cleaned_count = 0
    for task in tasks:
        is_completed = task.get("completed", False)
        try:
            task_date = datetime.strptime(task.get("date"), "%Y-%m-%d")
            if not is_completed or task_date.date() >= start_of_this_week.date():
                tasks_to_keep.append(task)
            else:
                cleaned_count += 1
        except (ValueError, TypeError):
            tasks_to_keep.append(task)
    
    if cleaned_count > 0:
        tasks = tasks_to_keep
        save_tasks()

# --- UI更新 ---
def refresh_treeview(filter_mode="all"):
    for item in tree.get_children():
        tree.delete(item)

    display_tasks = []
    if filter_mode == "this_week":
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        for task in tasks:
            try:
                task_date = datetime.strptime(task.get("date", ""), "%Y-%m-%d")
                if start_of_week.date() <= task_date.date() <= end_of_week.date():
                    display_tasks.append(task)
            except ValueError:
                continue
    else:
        display_tasks = tasks

    display_tasks.sort(key=lambda x: x.get("date", "9999-12-31"))

    for task in display_tasks:
        status_marker = "✔" if task.get("completed", False) else " "
        task_text = task.get("text", "")
        task_date = task.get("date", "N/A")
        task_rank = task.get("rank", "N/A").upper()

        tag = f"rank_{task_rank.lower()}" if task_rank in ["A", "B", "C"] else ""
        if task.get("completed", False):
            tag = "completed"
            
        unique_id = f"{task_text}_{task_date}_{task_rank}_{datetime.now().timestamp()}"
        tree.insert("", tk.END, iid=unique_id, values=(status_marker, task_text, task_date, task_rank), tags=(tag,))


# --- タスク操作関数 ---
def get_tasks_from_selection():
    selected_iids = tree.selection()
    selected_tasks = []
    for iid in selected_iids:
        values = tree.item(iid, 'values')
        for task in tasks:
            if task['text'] == values[1] and task['date'] == values[2] and task['rank'] == values[3]:
                if task not in selected_tasks:
                    selected_tasks.append(task)
    return selected_tasks

def add_task(event=None):
    task_text = entry_task.get()
    task_date = entry_date.get()
    task_rank = combo_rank.get()

    try:
        datetime.strptime(task_date, "%Y-%m-%d")
    except ValueError:
        messagebox.showwarning("警告", "日付はYYYY-MM-DD形式で入力してください。")
        return
        
    if task_text and task_date and task_rank:
        tasks.append({"text": task_text, "completed": False, "date": task_date, "rank": task_rank})
        save_tasks()
        refresh_treeview(filter_var.get())
        entry_task.delete(0, tk.END)
    else:
        messagebox.showwarning("警告", "すべての項目（タスク、日付、ランク）を入力してください。")

def delete_task():
    selected_tasks = get_tasks_from_selection()
    if not selected_tasks:
        messagebox.showwarning("警告", "削除するタスクを選択してください。")
        return

    for task_to_delete in selected_tasks:
        if task_to_delete in tasks:
            tasks.remove(task_to_delete)
    
    save_tasks()
    refresh_treeview(filter_var.get())

def toggle_complete_task(event=None):
    selected_tasks = get_tasks_from_selection()
    if not selected_tasks:
        return 

    for task in selected_tasks:
        task["completed"] = not task.get("completed", False)
    
    save_tasks()
    refresh_treeview(filter_var.get())

def edit_task():
    selected_tasks = get_tasks_from_selection()
    if not selected_tasks:
        messagebox.showwarning("警告", "編集するタスクを1つ選択してください。")
        return
    if len(selected_tasks) > 1:
        messagebox.showwarning("警告", "編集できるタスクは1つだけです。")
        return
    
    task_to_edit = selected_tasks[0]

    editor = tk.Toplevel(root)
    editor.title("タスクの編集")
    editor.geometry("380x200")

    tk.Label(editor, text="タスク:", font=DEFAULT_FONT).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    edit_entry_task = tk.Entry(editor, width=30, font=DEFAULT_FONT)
    edit_entry_task.insert(0, task_to_edit["text"])
    edit_entry_task.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(editor, text="日付 (YYYY-MM-DD):", font=DEFAULT_FONT).grid(row=1, column=0, padx=10, pady=10, sticky="w")
    edit_entry_date = tk.Entry(editor, width=20, font=DEFAULT_FONT)
    edit_entry_date.insert(0, task_to_edit["date"])
    edit_entry_date.grid(row=1, column=1, padx=10, pady=10)

    tk.Label(editor, text="ランク:", font=DEFAULT_FONT).grid(row=2, column=0, padx=10, pady=10, sticky="w")
    edit_combo_rank = ttk.Combobox(editor, values=["A", "B", "C"], state="readonly", font=DEFAULT_FONT)
    edit_combo_rank.set(task_to_edit["rank"])
    edit_combo_rank.grid(row=2, column=1, padx=10, pady=10)

    def save_edits():
        new_text = edit_entry_task.get()
        new_date = edit_entry_date.get()
        new_rank = edit_combo_rank.get()
        try:
            datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("警告", "日付はYYYY-MM-DD形式で入力してください。", parent=editor)
            return

        if new_text and new_date and new_rank:
            task_to_edit["text"] = new_text
            task_to_edit["date"] = new_date
            task_to_edit["rank"] = new_rank
            save_tasks()
            refresh_treeview(filter_var.get())
            editor.destroy()
        else:
            messagebox.showwarning("警告", "すべての項目は必須です。", parent=editor)

    save_button = tk.Button(editor, text="変更を保存", command=save_edits, font=DEFAULT_FONT)
    save_button.grid(row=3, column=0, columnspan=2, pady=10)

def carry_over_tasks():
    today = datetime.now()
    start_of_this_week = today - timedelta(days=today.weekday())
    end_of_last_week = start_of_this_week - timedelta(days=1)
    start_of_last_week = end_of_last_week - timedelta(days=6)

    new_date_str = start_of_this_week.strftime("%Y-%m-%d")
    carried_over_tasks = []

    for task in tasks:
        is_completed = task.get("completed", False)
        if not is_completed:
            try:
                task_date = datetime.strptime(task.get("date"), "%Y-%m-%d")
                if start_of_last_week.date() <= task_date.date() <= end_of_last_week.date():
                    task["date"] = new_date_str
                    carried_over_tasks.append(task["text"])
            except (ValueError, TypeError):
                continue

    if carried_over_tasks:
        save_tasks()
        refresh_treeview(filter_var.get())
        messagebox.showinfo("タスクの引き継ぎ", 
                            f"{len(carried_over_tasks)}件のタスクを今週に引き継ぎました:\n\n- " + "\n- ".join(carried_over_tasks))
    else:
        messagebox.showinfo("引き継ぎ対象なし", "先週の未完了タスクはありませんでした。")

def sort_column(col, reverse):
    try:
        data = [(tree.set(child, col), child) for child in tree.get_children('')]
    except tk.TclError:
        return

    data.sort(reverse=reverse)
    for index, (val, child) in enumerate(data):
        tree.move(child, '', index)

    tree.heading(col, command=lambda: sort_column(col, not reverse))


# --- 画面の作成 ---
root = tk.Tk()
root.title("週間ランクToDoリスト")
root.geometry("750x550")
root.configure(bg='#f0f0f0')

# --- Treeviewのスタイル設定 ---
style = ttk.Style(root)
style.configure("Treeview", font=DEFAULT_FONT, rowheight=25)
style.configure("Treeview.Heading", font=DEFAULT_FONT_BOLD)

# --- ウィジェットの作成と配置 ---
input_frame = tk.Frame(root, bg='#f0f0f0')
input_frame.pack(pady=10, padx=10, fill='x')

tk.Label(input_frame, text="タスク:", bg='#f0f0f0', font=DEFAULT_FONT).grid(row=0, column=0, padx=5, pady=5)
entry_task = tk.Entry(input_frame, width=30, font=DEFAULT_FONT)
entry_task.grid(row=0, column=1, padx=5, pady=5)
entry_task.bind("<Return>", add_task)

tk.Label(input_frame, text="日付 (YYYY-MM-DD):", bg='#f0f0f0', font=DEFAULT_FONT).grid(row=0, column=2, padx=5, pady=5)
entry_date = tk.Entry(input_frame, width=12, font=DEFAULT_FONT)
entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
entry_date.grid(row=0, column=3, padx=5, pady=5)

tk.Label(input_frame, text="ランク:", bg='#f0f0f0', font=DEFAULT_FONT).grid(row=0, column=4, padx=5, pady=5)
combo_rank = ttk.Combobox(input_frame, values=["A", "B", "C"], width=5, state="readonly", font=DEFAULT_FONT)
combo_rank.current(1)
combo_rank.grid(row=0, column=5, padx=5, pady=5)
add_button = tk.Button(input_frame, text="タスクを追加", command=add_task, font=DEFAULT_FONT)
add_button.grid(row=0, column=6, padx=10, pady=5)

filter_frame = tk.Frame(root, bg='#f0f0f0')
filter_frame.pack(pady=5, padx=10, fill='x')
filter_var = tk.StringVar(value="this_week")
tk.Radiobutton(filter_frame, text="すべてのタスク", variable=filter_var, value="all", command=lambda: refresh_treeview("all"), bg='#f0f0f0', font=DEFAULT_FONT).pack(side=tk.LEFT)
tk.Radiobutton(filter_frame, text="今週のタスク", variable=filter_var, value="this_week", command=lambda: refresh_treeview("this_week"), bg='#f0f0f0', font=DEFAULT_FONT).pack(side=tk.LEFT, padx=10)

tree_frame = tk.Frame(root)
tree_frame.pack(pady=10, padx=10, fill='both', expand=True)

columns = ("status", "task", "date", "rank")
tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode="extended")

tree.heading("status", text="✔", command=lambda: sort_column("status", False))
tree.heading("task", text="タスク", command=lambda: sort_column("task", False))
tree.heading("date", text="日付", command=lambda: sort_column("date", False))
tree.heading("rank", text="ランク", command=lambda: sort_column("rank", False))
tree.column("status", width=30, anchor=tk.CENTER)
tree.column("task", width=400)
tree.column("date", width=100, anchor=tk.CENTER)
tree.column("rank", width=50, anchor=tk.CENTER)
tree.tag_configure('rank_a', background='#ffdddd')
tree.tag_configure('rank_b', background='#fffbdd')
tree.tag_configure('rank_c', background='#ddffdd')
tree.tag_configure('completed', foreground='gray', font=(DEFAULT_FONT[0], DEFAULT_FONT[1], 'overstrike'))
scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
tree.pack(side='left', fill='both', expand=True)
scrollbar.pack(side='right', fill='y')
tree.bind("<Double-1>", toggle_complete_task)

button_frame = tk.Frame(root, bg='#f0f0f0')
button_frame.pack(pady=10)

carry_over_button = tk.Button(button_frame, text="未完了を引き継ぎ", command=carry_over_tasks, font=DEFAULT_FONT)
carry_over_button.pack(side=tk.LEFT, padx=5)

edit_button = tk.Button(button_frame, text="選択を編集", command=edit_task, font=DEFAULT_FONT)
edit_button.pack(side=tk.LEFT, padx=5)

complete_button = tk.Button(button_frame, text="完了/未完了", command=toggle_complete_task, font=DEFAULT_FONT)
complete_button.pack(side=tk.LEFT, padx=5)

delete_button = tk.Button(button_frame, text="選択を削除", command=delete_task, font=DEFAULT_FONT)
delete_button.pack(side=tk.LEFT, padx=5)

# --- アプリの起動 ---
load_tasks()
cleanup_old_completed_tasks()
refresh_treeview(filter_var.get())
root.mainloop()
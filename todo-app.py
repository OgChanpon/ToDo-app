import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, timedelta

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

        # Treeviewにタスクの辞書そのものを保持させる (iidにユニークなIDとして利用)
        tree.insert("", tk.END, iid=f"{task_text}_{task_date}", values=(status_marker, task_text, task_date, task_rank), tags=(tag,))

# --- タスク操作関数 ---
def get_tasks_from_selection():
    """選択されたTreeviewアイテムに対応するタスク辞書のリストを返す"""
    selected_iids = tree.selection()
    selected_tasks = []
    for iid in selected_iids:
        values = tree.item(iid, 'values')
        for task in tasks:
            # 複合キー (text+date) でタスクを特定
            if task['text'] == values[1] and task['date'] == values[2]:
                if task not in selected_tasks: # 重複を避ける
                    selected_tasks.append(task)
                break
    return selected_tasks

def add_task(event=None):
    task_text = entry_task.get()
    task_date = entry_date.get()
    task_rank = combo_rank.get()

    try:
        datetime.strptime(task_date, "%Y-%m-%d")
    except ValueError:
        messagebox.showwarning("Warning", "Date must be in YYYY-MM-DD format.")
        return
        
    if task_text and task_date and task_rank:
        tasks.append({"text": task_text, "completed": False, "date": task_date, "rank": task_rank})
        save_tasks()
        refresh_treeview(filter_var.get())
        entry_task.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "Please fill in all fields (Task, Date, Rank).")

def delete_task():
    selected_tasks = get_tasks_from_selection()
    if not selected_tasks:
        messagebox.showwarning("Warning", "Please select task(s) to delete.")
        return

    # フィルタリングされたリストから安全に削除するために、元のtasksリストから削除する
    for task_to_delete in selected_tasks:
        if task_to_delete in tasks:
            tasks.remove(task_to_delete)
    
    save_tasks()
    refresh_treeview(filter_var.get())

def toggle_complete_task(event=None):
    selected_tasks = get_tasks_from_selection()
    if not selected_tasks:
        return # メッセージなしでサイレントに終了

    for task in selected_tasks:
        task["completed"] = not task.get("completed", False)
    
    save_tasks()
    refresh_treeview(filter_var.get())

def edit_task():
    selected_tasks = get_tasks_from_selection()
    if not selected_tasks:
        messagebox.showwarning("Warning", "Please select one task to edit.")
        return
    if len(selected_tasks) > 1:
        messagebox.showwarning("Warning", "Please select only one task to edit.")
        return
    
    task_to_edit = selected_tasks[0]

    # 編集用の新しいウィンドウを作成
    editor = tk.Toplevel(root)
    editor.title("Edit Task")
    editor.geometry("350x200")

    tk.Label(editor, text="Task:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    edit_entry_task = tk.Entry(editor, width=30)
    edit_entry_task.insert(0, task_to_edit["text"])
    edit_entry_task.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(editor, text="Date (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    edit_entry_date = tk.Entry(editor, width=20)
    edit_entry_date.insert(0, task_to_edit["date"])
    edit_entry_date.grid(row=1, column=1, padx=10, pady=10)

    tk.Label(editor, text="Rank:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    edit_combo_rank = ttk.Combobox(editor, values=["A", "B", "C"], state="readonly")
    edit_combo_rank.set(task_to_edit["rank"])
    edit_combo_rank.grid(row=2, column=1, padx=10, pady=10)

    def save_edits():
        new_text = edit_entry_task.get()
        new_date = edit_entry_date.get()
        new_rank = edit_combo_rank.get()
        try:
            datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Warning", "Date must be in YYYY-MM-DD format.", parent=editor)
            return

        if new_text and new_date and new_rank:
            task_to_edit["text"] = new_text
            task_to_edit["date"] = new_date
            task_to_edit["rank"] = new_rank
            save_tasks()
            refresh_treeview(filter_var.get())
            editor.destroy()
        else:
            messagebox.showwarning("Warning", "All fields are required.", parent=editor)

    save_button = tk.Button(editor, text="Save Changes", command=save_edits)
    save_button.grid(row=3, column=0, columnspan=2, pady=10)

def sort_column(col, reverse):
    """Treeviewのカラムヘッダーがクリックされたときにソートを実行する"""
    try:
        data = [(tree.set(child, col), child) for child in tree.get_children('')]
    except tk.TclError:
        # 無効な列名の場合のエラーを無視
        return

    # データ型に応じてソート
    data.sort(reverse=reverse)
    for index, (val, child) in enumerate(data):
        tree.move(child, '', index)

    # 次回のクリックで逆順ソートするようにコマンドを更新
    tree.heading(col, command=lambda: sort_column(col, not reverse))

# --- 画面の作成 ---
root = tk.Tk()
root.title("Weekly Ranked ToDo List")
root.geometry("650x550")
root.configure(bg='#f0f0f0')

# --- ウィジェットの作成 ---
# (中身は前回とほぼ同じ... )
# ... (入力フレーム、フィルタフレームなど)

# Treeview (タスクリスト) - selectmodeの変更
tree_frame = tk.Frame(root)
tree_frame.pack(pady=10, padx=10, fill='both', expand=True)
columns = ("status", "task", "date", "rank")
tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode="extended")
# ... (ヘッディングとカラムの設定)
# ...
# 以下、上記コードを参考にして入力フレーム、フィルタフレーム、ボタンフレームを配置
# 入力フレーム
input_frame = tk.Frame(root, bg='#f0f0f0')
input_frame.pack(pady=10, padx=10, fill='x')
tk.Label(input_frame, text="Task:", bg='#f0f0f0').grid(row=0, column=0, padx=5, pady=5)
entry_task = tk.Entry(input_frame, width=30, font=('Helvetica', 10))
entry_task.grid(row=0, column=1, padx=5, pady=5)
entry_task.bind("<Return>", add_task) # エンターキーのバインド

tk.Label(input_frame, text="Date (YYYY-MM-DD):", bg='#f0f0f0').grid(row=0, column=2, padx=5, pady=5)
entry_date = tk.Entry(input_frame, width=12, font=('Helvetica', 10))
entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
entry_date.grid(row=0, column=3, padx=5, pady=5)

tk.Label(input_frame, text="Rank:", bg='#f0f0f0').grid(row=0, column=4, padx=5, pady=5)
combo_rank = ttk.Combobox(input_frame, values=["A", "B", "C"], width=5, state="readonly")
combo_rank.current(1)
combo_rank.grid(row=0, column=5, padx=5, pady=5)
add_button = tk.Button(input_frame, text="Add Task", command=add_task)
add_button.grid(row=0, column=6, padx=10, pady=5)

# フィルタフレーム
filter_frame = tk.Frame(root, bg='#f0f0f0')
filter_frame.pack(pady=5, padx=10, fill='x')
filter_var = tk.StringVar(value="this_week") # デフォルトを「今週」に変更
tk.Radiobutton(filter_frame, text="All Tasks", variable=filter_var, value="all", command=lambda: refresh_treeview("all"), bg='#f0f0f0').pack(side=tk.LEFT)
tk.Radiobutton(filter_frame, text="This Week's Tasks", variable=filter_var, value="this_week", command=lambda: refresh_treeview("this_week"), bg='#f0f0f0').pack(side=tk.LEFT, padx=10)

# Treeview本体とスクロールバー
tree.heading("status", text="✔", command=lambda: sort_column("status", False))
tree.heading("task", text="Task", command=lambda: sort_column("task", False))
tree.heading("date", text="Date", command=lambda: sort_column("date", False))
tree.heading("rank", text="Rank", command=lambda: sort_column("rank", False))
tree.column("status", width=30, anchor=tk.CENTER)
tree.column("task", width=350)
tree.column("date", width=100, anchor=tk.CENTER)
tree.column("rank", width=50, anchor=tk.CENTER)
tree.tag_configure('rank_a', background='#ffdddd')
tree.tag_configure('rank_b', background='#fffbdd')
tree.tag_configure('rank_c', background='#ddffdd')
tree.tag_configure('completed', foreground='gray', font=('Helvetica', 10, 'overstrike'))
scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
tree.pack(side='left', fill='both', expand=True)
scrollbar.pack(side='right', fill='y')
tree.bind("<Double-1>", toggle_complete_task) # ダブルクリックのバインド

# ボタンフレーム
button_frame = tk.Frame(root, bg='#f0f0f0')
button_frame.pack(pady=10)
edit_button = tk.Button(button_frame, text="Edit Selected", command=edit_task)
edit_button.pack(side=tk.LEFT, padx=5)
complete_button = tk.Button(button_frame, text="Toggle Complete", command=toggle_complete_task)
complete_button.pack(side=tk.LEFT, padx=5)
delete_button = tk.Button(button_frame, text="Delete Selected", command=delete_task)
delete_button.pack(side=tk.LEFT, padx=5)

# --- アプリの起動 ---
load_tasks()
refresh_treeview(filter_var.get())
root.mainloop()
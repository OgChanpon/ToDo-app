import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os

# --- データ管理 ---
FILENAME = "tasks.json"
tasks = []

def load_tasks():
    """アプリ起動時にJSONファイルからタスクを読み込む"""
    global tasks
    if os.path.exists(FILENAME):
        with open(FILENAME, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    else:
        tasks = []

def save_tasks():
    """タスクリストをJSONファイルに保存する"""
    with open(FILENAME, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

# --- UI更新 ---
def refresh_listbox():
    """タスクリストの変更をUIに反映する"""
    listbox.delete(0, tk.END) # 現在のリストをクリア
    for i, task in enumerate(tasks):
        # タスクのテキストと状態を整形して表示
        text = task["text"]
        status_marker = "✔" if task["completed"] else " "
        display_text = f"[{status_marker}] {text}"
        
        listbox.insert(tk.END, display_text)
        
        # 完了状態に応じて見た目を変更
        if task["completed"]:
            listbox.itemconfig(i, {'fg': 'gray'}) # 文字色をグレーに
            listbox.itemconfig(i, {'font': ('Helvetica', 10, 'overstrike')}) # 取り消し線
        else:
            listbox.itemconfig(i, {'fg': 'black'})
            listbox.itemconfig(i, {'font': ('Helvetica', 10)})

# --- タスク操作関数 ---
def add_task():
    """タスクを追加する"""
    task_text = entry.get()
    if task_text:
        tasks.append({"text": task_text, "completed": False})
        save_tasks()
        refresh_listbox()
        entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "Please enter a task.")

def delete_task():
    """選択したタスクを削除する"""
    selected_indices = listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Warning", "Please select the task to delete.")
        return

    # 逆順で削除しないとインデックスがずれる
    for index in reversed(selected_indices):
        tasks.pop(index)

    save_tasks()
    refresh_listbox()

def edit_task():
    """選択したタスクを編集する"""
    selected_indices = listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Warning", "Please select the task you wish to edit.")
        return
    
    # 複数選択は考慮せず、最初の1つを編集対象とする
    index = selected_indices[0]
    task_text = tasks[index]["text"]

    # simpledialogを使って新しいタスク名を入力させる
    new_task_text = simpledialog.askstring("Edit Task", "Please enter a new task name:",
                                           initialvalue=task_text)

    if new_task_text:
        tasks[index]["text"] = new_task_text
        save_tasks()
        refresh_listbox()

def toggle_complete_task(event):
    """タスクの完了/未完了を切り替える (ダブルクリックで呼び出し)"""
    selected_indices = listbox.curselection()
    if not selected_indices:
        return
    
    index = selected_indices[0]
    tasks[index]["completed"] = not tasks[index]["completed"]
    save_tasks()
    refresh_listbox()

# --- 画面の作成 ---
root = tk.Tk()
root.title("ToDo List")
root.geometry("400x450")

# --- ウィジェットの作成と配置 ---
frame = tk.Frame(root)
frame.pack(pady=10)

entry = tk.Entry(frame, width=30, font=('Helvetica', 12))
entry.pack(side=tk.LEFT, padx=5)

add_button = tk.Button(frame, text="Add Task", command=add_task)
add_button.pack(side=tk.LEFT)

# スクロールバー付きのリストボックス
list_frame = tk.Frame(root)
list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(list_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

listbox = tk.Listbox(list_frame, height=15, font=('Helvetica', 12), yscrollcommand=scrollbar.set)
listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
listbox.bind("<Double-1>", toggle_complete_task) # ダブルクリックイベントに関数を紐付け

scrollbar.config(command=listbox.yview)

# 編集・削除ボタン用のフレーム
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

edit_button = tk.Button(button_frame, text="Edit Selected Task", command=edit_task)
edit_button.pack(side=tk.LEFT, padx=5)

delete_button = tk.Button(button_frame, text="Delete selected tasks", command=delete_task)
delete_button.pack(side=tk.LEFT, padx=5)


# --- アプリの起動 ---
load_tasks()
refresh_listbox()
root.mainloop()
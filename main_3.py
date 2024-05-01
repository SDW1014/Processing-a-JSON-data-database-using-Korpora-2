
import os
import glob
import json
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from nltk.tokenize import word_tokenize

# 데이터베이스 연결 및 테이블 생성
conn = sqlite3.connect('text_data.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS tokenized_texts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_name TEXT,
    doc_id INTEGER,
    text TEXT,
    word TEXT,
    position INTEGER
)
''')
conn.commit()

def list_files(frame):
    for widget in frame.winfo_children():
        widget.destroy()
    c.execute("SELECT DISTINCT folder_name FROM tokenized_texts")
    for folder_name in c.fetchall():
        row_frame = tk.Frame(frame)
        row_frame.pack(fill='x')
        tk.Label(row_frame, text=folder_name[0]).pack(side='left')
        tk.Button(row_frame, text="Delete", command=lambda f=folder_name[0]: delete_data(f)).pack(side='right')

def delete_data(folder_name):
    c.execute("DELETE FROM tokenized_texts WHERE folder_name=?", (folder_name,))
    conn.commit()
    messagebox.showinfo("Success", f"Data for folder '{folder_name}' has been deleted.")
    list_files(frame_files)

def load_data_to_database(folder_path, progress_var, status_label, root):
    json_files = glob.glob(os.path.join(folder_path, '*.json'))
    total_files = len(json_files)
    folder_name.set(os.path.basename(folder_path))
    progress_var.set(0)
    status_label.config(text=f"Loading data... 0/{total_files}")
    root.update_idletasks()

    for i, json_file in enumerate(json_files, start=1):
        try:
            with open(json_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Load Error", f"An error occurred while loading {json_file}: {e}")
            continue  # 오류가 발생한 파일을 건너뛰고 계속 진행

        doc_id = os.path.basename(json_file).split('.')[0]
        for info in data.get('info', []):
            if 'annotations' in info and 'text' in info['annotations']:
                text = info['annotations']['text']
                tokens = word_tokenize(text)
                for pos, word in enumerate(tokens):
                    c.execute('''
                        INSERT INTO tokenized_texts (folder_name, doc_id, text, word, position)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (folder_name.get(), doc_id, text, word, pos))
        conn.commit()
        progress_var.set(i)
        status_label.config(text=f"Loading data... {i}/{total_files}")
        root.update_idletasks()
    messagebox.showinfo("Success", f"Data for folder '{folder_name.get()}' loaded successfully.")

def select_folder(progress_var, status_label, root, frame):
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        load_data_to_database(folder_selected, progress_var, status_label, root)
    list_files(frame)

# GUI 설정
root = tk.Tk()
root.title("Data Loader")

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", variable=progress_var)
progress_bar.pack(pady=10)

status_label = tk.Label(root, text="Select a folder to start loading data.")
status_label.pack(pady=5)

frame_files = tk.Frame(root)
frame_files.pack(fill='both', expand=True)

btn_select_folder = tk.Button(root, text="Select Folder and Load Data", command=lambda: select_folder(progress_var, status_label, root, frame_files))
btn_select_folder.pack(pady=20)

list_files(frame_files)  # 이 함수 호출은 모든 관련 함수가 정의된 후에 수행

root.mainloop()

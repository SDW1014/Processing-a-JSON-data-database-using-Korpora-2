
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

def check_folder_exists(folder_name):
    c.execute("SELECT COUNT(*) FROM tokenized_texts WHERE folder_name=?", (folder_name,))
    return c.fetchone()[0] > 0

def load_data_to_database(folder_path, progress_var, status_label, root, folder_name_var):
    folder_name = os.path.basename(folder_path)
    folder_name_var.set(folder_name)
    if check_folder_exists(folder_name):
        messagebox.showwarning("Warning", f"Data for folder '{folder_name}' already exists. Delete it first.")
        return

    json_files = glob.glob(os.path.join(folder_path, '*.json'))
    total_files = len(json_files)
    progress_var.set(0)  # 초기 진행률을 0으로 설정
    progress_bar['maximum'] = total_files  # 프로그레스바의 최대값을 파일 수로 설정

    status_label.config(text=f"Loading data... 0/{total_files}")
    root.update_idletasks()

    for i, json_file in enumerate(json_files, start=1):
        try:
            with open(json_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Load Error", f"An error occurred while loading {json_file}: {e}")
            continue

        doc_id = os.path.basename(json_file).split('.')[0]
        for info in data.get('info', []):
            if 'annotations' in info and 'text' in info['annotations']:
                text = info['annotations']['text']
                tokens = word_tokenize(text)
                for pos, word in enumerate(tokens):
                    c.execute('''
                        INSERT INTO tokenized_texts (folder_name, doc_id, text, word, position)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (folder_name, doc_id, text, word, pos))
        conn.commit()
        progress_var.set(i)  # 각 파일 처리 후 진행 상태 업데이트
        status_label.config(text=f"Loading data... {i}/{total_files}")
        root.update_idletasks()
    messagebox.showinfo("Success", f"Data for folder '{folder_name}' loaded successfully.")


def fetch_data(keyword):
    query = """
    SELECT word, COUNT(*) AS frequency
    FROM (
        SELECT doc_id, position + 1 AS next_position
        FROM tokenized_texts
        WHERE word = ?
    ) AS next_pos
    JOIN tokenized_texts AS next_word
    ON next_pos.doc_id = next_word.doc_id AND next_pos.next_position = next_word.position
    GROUP BY word
    ORDER BY frequency DESC
    LIMIT 5;
    """
    c.execute(query, (keyword,))
    return c.fetchall()

def show_results(entry_keyword, listbox_results):
    keyword = entry_keyword.get()
    if not keyword.strip():
        messagebox.showwarning("Warning", "Please enter a keyword.")
        return
    results = fetch_data(keyword)
    listbox_results.delete(0, tk.END)
    for word, freq in results:
        listbox_results.insert(tk.END, f"Word: {word}, Frequency: {freq}")

def select_folder(progress_var, status_label, root, frame_files, folder_name_var):
    folder_path = filedialog.askdirectory()
    if folder_path:
        load_data_to_database(folder_path, progress_var, status_label, root, folder_name_var)
        list_files(frame_files)

# GUI 설정
root = tk.Tk()
root.title("Data Loader and Searcher")

# 탭 설정
notebook = ttk.Notebook(root)
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
notebook.add(tab1, text="Load Data")
notebook.add(tab2, text="Search Data")
notebook.pack(expand=1, fill='both')

# 탭 1 (데이터 로드)
progress_var = tk.IntVar()
folder_name_var = tk.StringVar()

progress_bar = ttk.Progressbar(tab1, orient="horizontal", length=300, mode="determinate", variable=progress_var)
progress_bar.pack(pady=10)

status_label = tk.Label(tab1, text="Select a folder to start loading data.")
status_label.pack(pady=5)

frame_files = tk.Frame(tab1)
frame_files.pack(fill='both', expand=True)

btn_select_folder = tk.Button(tab1, text="Select Folder and Load Data", command=lambda: select_folder(progress_var, status_label, root, frame_files, folder_name_var))
btn_select_folder.pack(pady=20)

list_files(frame_files)
 
# 탭 2 (키워드 검색)
tk.Label(tab2, text="Enter Keyword:").pack(pady=10)
entry_keyword = tk.Entry(tab2)
entry_keyword.pack()
button_show = tk.Button(tab2, text="Show Results", command=lambda: show_results(entry_keyword, listbox_results))
button_show.pack(pady=10)
listbox_results = tk.Listbox(tab2, height=5)
listbox_results.pack(pady=10)

root.mainloop()

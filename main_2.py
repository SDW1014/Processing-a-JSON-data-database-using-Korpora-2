
import os
import glob
import json
import sqlite3
from nltk.tokenize import word_tokenize
from collections import Counter

# 데이터베이스 연결 및 테이블 생성
conn = sqlite3.connect('text_data.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS tokenized_texts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER,
    text TEXT,
    word TEXT,
    position INTEGER
)
''')
conn.commit()

def load_data_to_database(json_file):
    """ JSON 데이터를 읽고 데이터베이스에 저장하는 함수 """
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from {json_file}: {e}")
        return

    doc_id = os.path.basename(json_file).split('.')[0]  # 파일 이름에서 doc_id 추출
    
    if 'info' in data:
        for info in data['info']:
            if 'annotations' in info and 'text' in info['annotations']:
                text = info['annotations']['text']
                tokens = word_tokenize(text)
                for pos, word in enumerate(tokens):
                    c.execute('INSERT INTO tokenized_texts (doc_id, text, word, position) VALUES (?, ?, ?, ?)',
                              (doc_id, text, word, pos))
    conn.commit()

def query_next_words(key):
    """ 주어진 키워드 다음에 나오는 단어를 조회하는 함수 """
    query = '''
    SELECT word, COUNT(*) as frequency
    FROM tokenized_texts
    WHERE position = (SELECT position + 1 FROM tokenized_texts WHERE word = ? LIMIT 1)
    GROUP BY word
    ORDER BY frequency DESC
    LIMIT 5
    '''
    c.execute(query, (key,))
    results = c.fetchall()
    print(f"Most frequent words after '{key}':", results)

# 폴더 경로 설정 및 파일 처리
folder_paths = ['D:/020.주제별 텍스트 일상 대화 데이터/01.데이터/1.Training/라벨링데이터/TL_01. KAKAO(1)']
for folder_path in folder_paths:
    json_files = glob.glob(os.path.join(folder_path, '*.json'))
    for json_file in json_files:
        load_data_to_database(json_file)

# 키워드 다음 단어 조회
query_next_words('지금')

# 데이터베이스 연결 종료
conn.close()

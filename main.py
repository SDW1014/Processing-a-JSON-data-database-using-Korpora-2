
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from Korpora import Korpora
from ttkthemes import ThemedStyle
import networkx as nx
import os
import pandas as pd  # Add this import for Excel manipulation

# 환경변수 설정 (yes를 자동으로 응답)
os.environ["KORPORA_ACCEPT_LOAD"] = "yes"  # 'yes' 자동 응답 설정

# 한글 폰트 설정
font_path = "C:/Windows/Fonts/malgun.ttf"  # 'Malgun Gothic' 폰트 경로
plt.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()  # Matplotlib 폰트 설정

# 말뭉치 다운로드 함수
def download_corpus(corpus_name):
    try:
        Korpora.fetch(corpus_name)  # 말뭉치 다운로드
        messagebox.showinfo("다운로드 완료", f"{corpus_name} 데이터셋이 다운로드되었습니다.")
    except Exception as e:
        if "does not support" in str(e):
            corpus_path = os.path.join(os.path.expanduser("~"), "Korpora", corpus_name)
            messagebox.showwarning(
                "압축 해제 필요",
                f"윈도우에서는 {corpus_name} 말뭉치를 수동으로 압축 해제해야 합니다.\n"
                f"경로: {corpus_path}",
            )
        else:
            messagebox.showerror("다운로드 오류", f"오류: {e}")

# 키워드 분석 및 그래프 생성 함수
def analyze_and_plot(corpus_name, keyword):
    try:
        corpus = Korpora.load(corpus_name)  # 말뭉치 로드
        word_count = {}  # 단어 빈도 분석을 위한 사전

        # 텍스트 가져오기
        texts = corpus.get_all_texts()  # 말뭉치 내 모든 텍스트
        for text in texts:
            words = text.split()  # 단어 분할
            for i, word in enumerate(words[:-1]):
                if word == keyword:
                    next_word = words[i + 1]
                    if next_word in word_count:
                        word_count[next_word] += 1
                    else:
                        word_count[next_word] = 1

        # 가장 빈도가 높은 단어 추출
        most_common = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:5]

        # 마인드맵 그래프 생성
        G = nx.Graph()
        G.add_node(keyword)
        for word, count in most_common:
            G.add_edge(keyword, word, weight=count)

        # 노드 라벨 설정
        node_labels = {keyword: f"{keyword}\n(1)"}
        for word, count in most_common:
            node_labels[word] = f"{word}\n({count})"

        # 그래프 그리기
        fig, ax = plt.subplots(figsize=(8, 6))
        pos = nx.spring_layout(G, k=0.5, iterations=50)

        # 노드 크기 및 라벨 설정
        node_sizes = [2500] + [2000 + 500 * count for _, count in most_common]

        # 그래프 그리기
        nx.draw(
            G,
            pos,
            with_labels=True,
            labels=node_labels,
            node_size=node_sizes,
            node_color="skyblue",
            font_size=12,
            font_family="Malgun Gothic",
            edge_color='black',
            arrows=False,
        )

        ax.set_facecolor("#2C2C2C")  # 배경색 설정
        ax.set_title(f"'{keyword}' 이후 가장 많이 나오는 단어 (마인드맵)")

        return fig, most_common  # 그래프와 가장 빈도가 높은 단어 리스트 반환

    except Exception as e:
        messagebox.showerror("분석 오류", f"분석 중 오류가 발생했습니다: {e}")
        return None, None

# 애플리케이션 설정
class CorpusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Korpora 말뭉치 분석")

        # 폰트 설정
        self.font = Font(family="Malgun Gothic", size=12)

        # 테마 설정
        self.style = ThemedStyle(self)
        self.style.theme_use('equilux')  # 어두운 테마

        # 메인 프레임
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 말뭉치 설명 레이블
        description_label = ttk.Label(
            main_frame,
            text="다음 말뭉치 중 하나를 선택하고, 분석할 키워드를 입력하세요.",
            font=self.font,
        )
        description_label.grid(row=0, columnspan=2, padx=5, pady=5, sticky="w")

        # 말뭉치 리스트 및 콤보박스
        corpus_label = ttk.Label(main_frame, text="말뭉치 선택:", font=self.font)
        corpus_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        corpus_list = Korpora.corpus_list()  # 코퍼스 목록 가져오기
        self.corpus_listbox = ttk.Combobox(main_frame, values=list(corpus_list.keys()), state="readonly", font=self.font)
        self.corpus_listbox.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # 키워드 입력 레이블 및 엔트리
        keyword_label = ttk.Label(main_frame, text="키워드 입력:", font=self.font)
        keyword_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.keyword_entry = ttk.Entry(main_frame, font=self.font)
        self.keyword_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # 'Show' 및 'Export' 버튼
        self.show_button = ttk.Button(main_frame, text="Show", command=self.show_graph)
        self.show_button.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        self.export_button = ttk.Button(main_frame, text="Export", command=self.export_to_excel)
        self.export_button.grid(row=3, column=1, padx=5, pady=5, sticky="e")

        # 로딩 레이블
        self.loading_label = ttk.Label(main_frame, text="", font=self.font)

        # 로딩 프로그레스 바
        self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')

        # 그래프 표시용 프레임
        self.graph_frame = ttk.Frame(main_frame)
        self.graph_frame.grid(row=4, columnspan=2, padx=5, pady=5, sticky="nsew")

        # 윈도우 크기 변형 시 그래프 리사이즈
        self.graph_frame.bind("<Configure>", self.resize_graph)

    # 그래프 표시 및 인터랙션 활성화
    def show_graph(self):
        corpus_name = self.corpus_listbox.get()  # 선택된 말뭉치
        keyword = self.keyword_entry.get()  # 입력된 키워드

        if corpus_name and keyword:
            # 버튼 비활성화
            self.show_button.config(state="disabled")

            # 로딩 표시
            self.loading_label.config(text="로딩 중...")
            self.loading_label.grid(row=5, columnspan=2, pady=5)

            self.progress_bar.grid(row=6, columnspan=2, pady=5)
            self.progress_bar.start()

            fig, most_common = analyze_and_plot(corpus_name, keyword)  # 그래프 및 단어 리스트 생성
            if fig:
                # 기존 캔버스 제거
                for widget in self.graph_frame.winfo_children():
                    widget.destroy()

                # 그래프 표시
                self.canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
                self.canvas.draw()

                # 인터랙티브 기능 활성화
                self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                self.canvas.mpl_connect("button_press_event", self.on_click)  # 클릭 이벤트 핸들링
                self.canvas.mpl_connect("scroll_event", self.on_scroll)  # 스크롤 확대/축소

                # 저장할 데이터 저장
                self.most_common_data = most_common

            # 로딩 표시 해제
            self.loading_label.grid_forget()
            self.progress_bar.stop()
            self.progress_bar.grid_forget()

            # 버튼 다시 활성화
            self.show_button.config(state="normal")
        else:
            messagebox.showwarning("입력 오류", "말뭉치와 키워드를 모두 선택하세요.")

    # 그래프 리사이즈
    def resize_graph(self, event):
        if hasattr(self, "canvas"):
            self.canvas.draw()  # 그래프 재그리기

    # 클릭 이벤트 핸들링 (그래프 드래그 지원)
    def on_click(self, event):
        if event.dblclick:
            self.canvas.figure.gca().set_xlim(auto=True)  # 더블 클릭으로 자동 리셋
            self.canvas.figure.gca().set_ylim(auto=True)
            self.canvas.draw()

    # 스크롤 이벤트 핸들링 (그래프 확대/축소)
    def on_scroll(self, event):
        ax = self.canvas.figure.gca()
        scale = 1.1 if event.button == "up" else 0.9  # 확대/축소 비율
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        ax.set_xlim([x * scale for x in xlim])  # x 축 조정
        ax.set_ylim([y * scale for y in ylim])  # y 축 조정

        self.canvas.draw()  # 그래프 재그리기

    # Excel로 데이터 내보내기
    def export_to_excel(self):
        if hasattr(self, "most_common_data"):
            filename = tk.filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            if filename:
                df = pd.DataFrame(self.most_common_data, columns=["Word", "Frequency"])
                df.to_excel(filename, index=False)
                messagebox.showinfo("Export", "Data exported successfully.")
        else:
            messagebox.showwarning("Export", "No data to export.")

# 애플리케이션 실행
if __name__ == "__main__":
    app = CorpusApp()  # GUI 애플리케이션 생성
    app.mainloop()  # 메인 루프 실행

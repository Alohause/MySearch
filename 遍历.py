import os
import jieba
import math
import warnings
import pdfplumber
from collections import defaultdict, Counter

warnings.filterwarnings("ignore", message=".*pkg_resources.*")
jieba.setLogLevel(jieba.logging.ERROR)

class RankedSearchEngine:
    def __init__(self, stop_words_file='stopwords.txt'):
        self.documents = {}
        self.doc_paths = {}
        self.doc_titles = {}
        self.doc_freq = defaultdict(int)
        self.doc_term_freqs = {}
        self.total_docs = 0
        self.stop_words = self._load_stop_words(stop_words_file)

    def _load_stop_words(self, file_path):
        loaded = set()
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded = {line.strip() for line in f if line.strip()}
            except:
                pass
        return loaded

    def add_document(self, doc_id, text, file_path, title):
        self.documents[doc_id] = text
        self.doc_paths[doc_id] = file_path
        self.doc_titles[doc_id] = title
        self.total_docs += 1

        words = jieba.lcut(text)
        clean_words = [w for w in words if w not in self.stop_words and len(w.strip()) > 0]

        self.doc_term_freqs[doc_id] = {'counts': Counter(clean_words), 'length': len(clean_words)}
        for word in set(clean_words):
            self.doc_freq[word] += 1

    def _calculate_score(self, query_words, doc_id):
        score = 0.0
        doc_data = self.doc_term_freqs[doc_id]
        if doc_data['length'] == 0: return 0.0

        for word in query_words:
            term_count = doc_data['counts'].get(word, 0)
            if term_count == 0: continue
            tf = term_count / doc_data['length']
            docs_with_word = self.doc_freq.get(word, 0)
            idf = math.log10(self.total_docs / (docs_with_word + 1)) + 1.0
            score += tf * idf
        return score

    def search(self, query, top_k=3):
        query_words = jieba.lcut(query)
        query_words = [w for w in query_words if w not in self.stop_words and len(w.strip()) > 0]

        if not query_words: return []

        ranked_results = []
        for doc_id in self.documents:
            score = self._calculate_score(query_words, doc_id)
            if score > 0:
                ranked_results.append((doc_id, score))

        ranked_results.sort(key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in ranked_results[:top_k]:
            results.append({
                'score': round(score, 4),
                'title': self.doc_titles[doc_id],
                'path': self.doc_paths[doc_id],
                'content': self.documents[doc_id]
            })
        return results

def extract_text_from_pdf(file_path):
    text_content = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"   正在解析: {os.path.basename(file_path)} ...")
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
    except Exception as e:
        print(f"   读取失败 {file_path}: {e}")
    return text_content

def read_file_content(file_path):

    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)

    encodings = ['utf-8', 'gbk', 'gb18030', 'utf-16']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                return f.read()
        except:
            continue
    return ""

def build_index_from_folder(folder_path, engine):
    print(f"正在扫描文件夹: {folder_path} ...")
    count = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.txt', '.md', '.py', '.pdf')):
                full_path = os.path.join(root, file)

                content = read_file_content(full_path)

                if len(content.strip()) > 0:
                    engine.add_document(doc_id=count, text=content, file_path=full_path, title=file)
                    count += 1
                    if count % 10 == 0:
                        print(f"   已索引 {count} 个文件...")

    print(f"索引构建完成，共索引了 {count} 个文件。\n")

if __name__ == "__main__":
    engine = RankedSearchEngine()

    target_folder = "C:/Users/Aloha/Desktop/文章"

    build_index_from_folder(target_folder, engine)

    while True:
        query = input("请输入搜索词 (输入q退出): ").strip()
        if query.lower() == 'q':
            break
        if not query:
            continue

        results = engine.search(query)

        print(f"\n找到 {len(results)} 个相关文件:")
        for res in results:
            print(f"[{res['title']}] ({res['score']})")
            print(f"   路径: {res['path']}")
            preview = res['content'][:50].replace('\n', ' ') + "..."
            print(f"   摘要: {preview}")
            print("\n")
        print("\n")
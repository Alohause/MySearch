import warnings
import os
import jieba
import math
from collections import defaultdict, Counter
# import self

warnings.filterwarnings("ignore", message=".*pkg_resources.*")
jieba.setLogLevel(jieba.logging.ERROR)

class RankedSearchEngine:
    def __init__(self, stop_words_file='stopwords.txt'):
        self.documents = {}
        self.doc_freq = defaultdict(int)
        self.doc_term_freqs = {}
        self.total_docs = 0
        self.stop_words = self._load_stop_words(stop_words_file)

    def _load_stop_words(self, file_path):
        loaded_words = set()
        if not os.path.exists(file_path):
            return loaded_words
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word: loaded_words.add(word)
        except:
            pass
        return loaded_words

    def add_document(self, doc_id, text):
        self.documents[doc_id] = text
        self.total_docs += 1
        words = jieba.lcut(text)
        clean_words = [w for w in words if w not in self.stop_words and len(w.strip()) > 0]
        term_counts = Counter(clean_words)
        self.doc_term_freqs[doc_id] = {'counts': term_counts, 'length': len(clean_words)}
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

    def search(self, query, top_k=5):
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
            results.append({'id': doc_id, 'score': round(score, 4), 'content': self.documents[doc_id]})
        return results

engine = RankedSearchEngine(stop_words_file='stopwords.txt')

engine.add_document(1, "人工智能是当今科技发展的重要方向，机器学习算法让计算机能够从数据中自动学习规律。深度学习作为机器学习的一个分支，在图像识别和自然语言处理领域取得了突破性进展。")
engine.add_document(2, "Python编程语言因其简洁易学和丰富的库支持，成为数据科学和人工智能开发的首选工具。NumPy和Pandas等库为数据处理提供了强大支持，TensorFlow和PyTorch则是深度学习的主流框架。")
engine.add_document(3, "搜索引擎技术基于信息检索原理，通过倒排索引和相关性排序算法快速找到用户需要的信息。Google和百度等商业搜索引擎采用了复杂的排名算法，包括PageRank和BERT等先进技术。")
engine.add_document(4, "大数据时代需要高效的数据处理技术，Hadoop和Spark提供了分布式计算解决方案。数据挖掘算法能从海量数据中发现有价值的信息模式，为商业决策提供支持。")

query = "算法"
print(f"正在搜索关键词: {query}...\n")
results = engine.search(query)

def highlight_text(text, query, color_code="\033[1;31m"):
    return text.replace(query, f"{color_code}{query}\033[0m")

if not results:
    print("没有找到结果。")
else:
    query_words = jieba.lcut(query)
    query_words = [w for w in query_words if w not in engine.stop_words and len(w.strip()) > 0]

    for i, res in enumerate(results):
        print(f"第 {i + 1} 条，{res['score']}")

        content = res['content']

        highlighted_content = content
        for word in query_words:
            highlighted_content = highlight_text(highlighted_content, word)
        print(f"内容: {highlighted_content}")

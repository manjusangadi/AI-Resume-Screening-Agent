import math
import re
from typing import List, Dict, Set

# Standard English stopwords to filter out from NLP calculations
STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should',
    "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't",
    'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
}

def tokenize(text: str) -> List[str]:
    """
    Cleans text, tokenizes into lower-case words, and removes punctuation.
    """
    # Lowercase
    text = text.lower()
    # Replace punctuation and special characters with spaces
    text = re.sub(r'[^a-z0-9\s\-\#\+]', ' ', text)
    # Split on spaces
    tokens = text.split()
    # Filter stopwords and short terms (length < 2, except things like C, R)
    cleaned_tokens = [
        t for t in tokens 
        if t not in STOPWORDS and (len(t) > 1 or t in {'c', 'r'})
    ]
    return cleaned_tokens

def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """
    Computes term frequency (TF) for a document.
    TF = count of term in doc / total terms in doc
    """
    tf = {}
    if not tokens:
        return tf
        
    for token in tokens:
        tf[token] = tf.get(token, 0.0) + 1.0
        
    total_tokens = len(tokens)
    for token in tf:
        tf[token] /= total_tokens
        
    return tf

def compute_idf(all_docs_tokens: List[List[str]]) -> Dict[str, float]:
    """
    Computes Inverse Document Frequency (IDF) across a corpus of tokenized documents.
    IDF = log(1 + (N / (1 + doc_freq_of_term)))
    """
    idf = {}
    total_docs = len(all_docs_tokens)
    if total_docs == 0:
        return idf
        
    # Get all unique words in the corpus
    unique_words = set(word for doc in all_docs_tokens for word in doc)
    
    # Count document frequency for each word
    for word in unique_words:
        doc_count = sum(1 for doc in all_docs_tokens if word in doc)
        # Add-one smoothing to avoid division by zero and negative logs
        idf[word] = math.log(1.0 + (total_docs / (1.0 + doc_count)))
        
    return idf

def vectorize(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    """
    Creates a sparse TF-IDF vector representation for a list of tokens based on pre-computed IDF.
    """
    tf = compute_tf(tokens)
    vector = {}
    for term, tf_val in tf.items():
        if term in idf:
            vector[term] = tf_val * idf[term]
    return vector

def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """
    Computes the cosine similarity between two sparse term-frequency/TF-IDF vectors.
    """
    # If either vector is empty, similarity is 0
    if not vec1 or not vec2:
        return 0.0
        
    # Find common terms (intersection)
    common_terms = set(vec1.keys()).intersection(set(vec2.keys()))
    
    # Compute dot product
    dot_product = sum(vec1[term] * vec2[term] for term in common_terms)
    
    # Compute magnitude (L2 Norm) for vec1
    mag1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
    
    # Compute magnitude (L2 Norm) for vec2
    mag2 = math.sqrt(sum(val ** 2 for val in vec2.values()))
    
    if mag1 == 0.0 or mag2 == 0.0:
        return 0.0
        
    return dot_product / (mag1 * mag2)

def calculate_nlp_similarity(doc_text: str, jd_text: str) -> float:
    """
    Helper function to directly compute Cosine Similarity between a document and the Job Description.
    """
    doc_tokens = tokenize(doc_text)
    jd_tokens = tokenize(jd_text)
    
    # Compute IDF over the mini-corpus of 2 documents
    corpus = [doc_tokens, jd_tokens]
    idf = compute_idf(corpus)
    
    # Vectorize
    doc_vec = vectorize(doc_tokens, idf)
    jd_vec = vectorize(jd_tokens, idf)
    
    return cosine_similarity(doc_vec, jd_vec)

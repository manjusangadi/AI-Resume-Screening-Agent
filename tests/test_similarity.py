import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.similarity import tokenize, compute_tf, compute_idf, vectorize, cosine_similarity, calculate_nlp_similarity

def test_tokenize():
    text = "Python Developer with machine learning, NLP, C++, and Docker!"
    tokens = tokenize(text)
    assert "python" in tokens
    assert "developer" in tokens
    assert "nlp" in tokens
    assert "docker" in tokens
    assert "and" not in tokens  # Stopword
    assert "with" not in tokens  # Stopword

def test_compute_tf():
    tokens = ["python", "machine", "python", "learning"]
    tf = compute_tf(tokens)
    assert tf["python"] == 0.5
    assert tf["machine"] == 0.25
    assert tf["learning"] == 0.25

def test_compute_idf():
    docs = [
        ["python", "machine", "learning"],
        ["python", "web", "development"],
        ["java", "spring", "boot"]
    ]
    idf = compute_idf(docs)
    assert "python" in idf
    assert "java" in idf
    # "python" appears in 2 docs, "java" in 1 doc. idf of java should be greater than python.
    assert idf["java"] > idf["python"]

def test_cosine_similarity():
    vec1 = {"python": 0.5, "learning": 0.3}
    vec2 = {"python": 0.4, "learning": 0.2, "docker": 0.9}
    sim = cosine_similarity(vec1, vec2)
    assert 0.0 <= sim <= 1.0
    
    # Zero vector similarity
    assert cosine_similarity({}, vec2) == 0.0

def test_calculate_nlp_similarity():
    doc = "Experienced python programmer specialized in natural language processing and deep learning."
    jd = "Seeking a python engineer with experience in deep learning and NLP."
    similarity = calculate_nlp_similarity(doc, jd)
    assert similarity > 0.0
    assert similarity <= 1.0

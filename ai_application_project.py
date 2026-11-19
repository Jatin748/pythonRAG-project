from pypdf import PdfReader
from dotenv import load_dotenv
from groq import Groq
import re
import math
from collections import Counter

# Load API key from .env file
load_dotenv()
client = Groq()


# Read TXT file
def read_txt(filename): # reads content from a txt file and returns then as a string
    with open(filename, "r") as file: #automatically closes the file when we use with even if an error occurs
        return file.read()


# Read PDF file
def read_pdf(filename): # reads content from a pdf file and returns them as a string by extracting text from each page and combining them into one string
    reader = PdfReader(filename)
    data = ""

    for page in reader.pages:
        data += page.extract_text() or ""

    return data


# Search keywords in document
def search_document(keyword, text): # returns sentences containing those sentences with keywords that are entered
    results = []
    data = text.lower()
    sentences = data.split(".")

    cleaned = [x.strip().lower() for x in keyword.split(',')]

    for sentence in sentences: # goes thorugh each sentence
        for word in cleaned: # goes through keywords in current sentence
            if word and word in sentence: # prevents an empty keyword from matching a sentence
                if sentence.strip() not in results: # prevents same sentence from being added twice
                    results.append(sentence.strip())

    return results, len(results)

# Split document into smaller chunks
def chunk_document(text, chunk_size=100, overlap=20):
    words = text.split()
    chunks = []

    step = chunk_size - overlap

    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks

# Create TF-IDF vectors for document chunks (term frequency inverse document frequency)
def build_tfidf(chunks):
    word_count = []
    document_frequency = {}

    for chunk in chunks:
        words = re.findall(r"\b\w+\b", chunk.lower())
        counts = Counter(words)
        word_count.append(counts)

        for word in set(words):
            document_frequency[word] = document_frequency.get(word, 0) + 1

    total_chunks = len(chunks)
    idf = {}

    for word, frequency in document_frequency.items():
        idf[word] = math.log((total_chunks + 1) / (frequency + 1)) + 1

    vectors = []

    for counts in word_count:
        vector = {}

        for word, count in counts.items():
            vector[word] = count * idf[word]

        vectors.append(vector)

    return idf, vectors

# Find the most relevant chunks for a question
def retrieve_chunks(question, chunks, idf, vectors, top_k=3):
    words = re.findall(r"\b\w+\b", question.lower())
    counts = Counter(words)

    query_vector = {}

    for word, count in counts.items():
        if word in idf:
            query_vector[word] = count * idf[word]

    scores = []

    for i, vector in enumerate(vectors):
        dot_product = sum(
            value * vector.get(word, 0)
            for word, value in query_vector.items()
        )

        query_length = math.sqrt(sum(v ** 2 for v in query_vector.values()))
        document_length = math.sqrt(sum(v ** 2 for v in vector.values()))

        if query_length == 0 or document_length == 0:
            similarity = 0
        else:
            similarity = dot_product / (query_length * document_length)

        scores.append((similarity, i))

    scores.sort(reverse=True)

    results = []

    for score, index in scores[:top_k]:
        if score > 0:
            results.append(chunks[index])

    return results

# Select document
file_type = input("Choose file type (txt/pdf): ").lower().strip()

if file_type == "txt":
    data = read_txt("data/suja_healthtech_dataset.txt")

elif file_type == "pdf":
    data = read_pdf("data/suja_healthtech_dataset.pdf")

else:
    print("Invalid file type")
    exit()

# Keyword search
keywordInput = input("Enter keywords to search: ").lower()

results, count = search_document(keywordInput, data)

if results:
    for sentence in results:
        print(sentence)

    print("Total matching sentences:", count)

else:
    print("Keyword not found")

# Remove practice questions from retrieval data
if "PRACTICE QUESTIONS" in data:
    data = data.split("PRACTICE QUESTIONS")[0]

# Create document chunks
chunks = chunk_document(data, chunk_size=250, overlap=50)

# Create TF-IDF index for searching chunks
idf, vectors = build_tfidf(chunks)

print("\nTotal document chunks:", len(chunks))
print("Document index created successfully!")

# Ask questions continuously
while True:

    askquestion = input("\nAsk a question (type exit to stop): ")

    if askquestion.lower().strip() == "exit":
        print("Program Exited")
        break

        # Find relevant chunks based on the question
    relevant_chunks = retrieve_chunks(
        askquestion, chunks, idf, vectors
    )
    
    print("\n--- RETRIEVED CHUNKS ---")

    for i, chunk in enumerate(relevant_chunks):
        print(f"\nChunk {i + 1}:")
        print(chunk)

    print("\n--- END OF RETRIEVED CHUNKS ---")

    if not relevant_chunks:
        print("No relevant information found in the document.")
        continue

    # Combine retrieved chunks into context
    context = "\n".join(relevant_chunks)

    # Send relevant context to Groq
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": f"""
                Answer using ONLY the information below.
                If the answer is unavailable, say:
                I don't know based on this document.

                Document Context:
                {context}

                Question:
                {askquestion}
                """
            }
        ]
    )

    print("\nAI Answer:")
    print(response.choices[0].message.content)
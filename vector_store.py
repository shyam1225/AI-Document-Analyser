from sentence_transformers import SentenceTransformer
import faiss


# Load embedding model only once
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def create_vector_store(chunks):

    embeddings = embedding_model.encode(
        chunks,
        convert_to_numpy=True
    )

    embeddings = embeddings.astype("float32")

    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return index


def find_relevant_chunks(chunks, question, index, k=3):

    question_embedding = embedding_model.encode(
        [question],
        convert_to_numpy=True
    )

    question_embedding = question_embedding.astype("float32")

    faiss.normalize_L2(question_embedding)

    scores, indices = index.search(
        question_embedding,
        k
    )

    relevant = []

    for i in indices[0]:

        if i >= 0:
            relevant.append(chunks[i])

    return relevant
"""Sample data loader for RAG Agent POC."""

from typing import List, Dict

def get_sample_documents(limit: int = None) -> List[Dict[str, str]]:
    """
    Return a list of sample documents for testing the RAG system.

    Each document is a dictionary with 'content' and 'metadata' fields.

    Args:
        limit: Optional limit on number of documents to return (useful for testing)

    Returns:
        List of document dictionaries
    """
    documents = [
        {
            "content": """
            Python is a high-level, interpreted programming language known for its simplicity
            and readability. Created by Guido van Rossum and first released in 1991, Python
            emphasizes code readability with its use of significant indentation. Python supports
            multiple programming paradigms, including structured, object-oriented, and functional
            programming. It has a comprehensive standard library and a vast ecosystem of
            third-party packages available through the Python Package Index (PyPI).
            """,
            "metadata": {"source": "python_basics", "topic": "python"}
        },
        {
            "content": """
            Machine Learning is a subset of artificial intelligence that enables systems to learn
            and improve from experience without being explicitly programmed. It focuses on the
            development of algorithms that can access data and use it to learn for themselves.
            There are three main types of machine learning: supervised learning, unsupervised
            learning, and reinforcement learning. Supervised learning uses labeled data to train
            models, while unsupervised learning finds patterns in unlabeled data.
            """,
            "metadata": {"source": "ml_intro", "topic": "machine_learning"}
        },
        {
            "content": """
            Deep Learning is a specialized subset of machine learning based on artificial neural
            networks with multiple layers. These networks are inspired by the structure and function
            of the human brain. Deep learning has revolutionized fields like computer vision, natural
            language processing, and speech recognition. Popular deep learning frameworks include
            TensorFlow, PyTorch, and Keras. Deep neural networks require large amounts of data and
            computational power to train effectively.
            """,
            "metadata": {"source": "deep_learning", "topic": "ai"}
        },
        {
            "content": """
            Natural Language Processing (NLP) is a branch of artificial intelligence that focuses
            on the interaction between computers and human language. NLP enables computers to
            understand, interpret, and generate human language in a valuable way. Common NLP tasks
            include text classification, named entity recognition, sentiment analysis, machine
            translation, and question answering. Modern NLP systems use transformer architectures
            like BERT, GPT, and T5 to achieve state-of-the-art results.
            """,
            "metadata": {"source": "nlp_overview", "topic": "nlp"}
        },
        {
            "content": """
            Large Language Models (LLMs) are neural networks trained on vast amounts of text data
            to understand and generate human-like text. Models like GPT-4, Claude, and PaLM have
            billions of parameters and can perform a wide range of language tasks without specific
            training. LLMs are trained using self-supervised learning on diverse internet text.
            They demonstrate emergent capabilities like few-shot learning, chain-of-thought reasoning,
            and complex instruction following. However, they can also produce incorrect information
            or exhibit biases present in their training data.
            """,
            "metadata": {"source": "llm_guide", "topic": "ai"}
        },
        {
            "content": """
            Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval
            with language model generation to improve the accuracy and relevance of AI responses.
            In a RAG system, relevant documents or passages are first retrieved from a knowledge
            base, then provided as context to a language model to generate a response. This approach
            helps reduce hallucinations, keeps information up-to-date, and allows the model to cite
            sources. RAG systems typically use vector databases and embedding models for efficient
            similarity search.
            """,
            "metadata": {"source": "rag_explanation", "topic": "rag"}
        },
        {
            "content": """
            Vector databases are specialized databases designed to store and query high-dimensional
            vectors efficiently. They are essential for similarity search in applications like
            recommendation systems, image search, and RAG systems. Popular vector databases include
            FAISS, Pinecone, Weaviate, and ChromaDB. These databases use techniques like approximate
            nearest neighbor (ANN) search to quickly find similar vectors in large datasets. Vector
            embeddings are typically generated using neural networks that encode semantic meaning.
            """,
            "metadata": {"source": "vector_db", "topic": "databases"}
        },
        {
            "content": """
            LangChain is a framework for developing applications powered by language models. It
            provides tools and abstractions for working with LLMs, including chains for combining
            multiple operations, agents for autonomous decision-making, and memory for maintaining
            conversation context. LangChain supports various LLM providers like OpenAI, Anthropic,
            and Google, and integrates with vector stores, document loaders, and other tools. It
            simplifies building complex LLM applications like chatbots, question-answering systems,
            and automated workflows.
            """,
            "metadata": {"source": "langchain_intro", "topic": "frameworks"}
        },
        {
            "content": """
            Embeddings are dense vector representations of data that capture semantic meaning in
            a continuous space. In NLP, word and sentence embeddings encode text into fixed-size
            vectors where similar meanings have similar vector representations. Common embedding
            models include Word2Vec, GloVe, and modern transformer-based models like BERT and
            sentence-transformers. Embeddings enable semantic search, clustering, and similarity
            comparisons. They are created by training neural networks on large text corpora to
            learn contextual relationships between words and phrases.
            """,
            "metadata": {"source": "embeddings_explained", "topic": "nlp"}
        },
        {
            "content": """
            Prompt engineering is the practice of designing and refining input prompts to get
            desired outputs from language models. Effective prompts can dramatically improve model
            performance on specific tasks. Techniques include few-shot learning (providing examples),
            chain-of-thought prompting (guiding reasoning steps), and system instructions that set
            the model's behavior. Good prompt engineering considers clarity, context, constraints,
            and the specific capabilities of the target model. It's becoming a crucial skill for
            working with LLMs in production applications.
            """,
            "metadata": {"source": "prompt_engineering", "topic": "ai"}
        }
    ]

    if limit is not None:
        return documents[:limit]
    return documents

def get_document_count() -> int:
    """Return the number of sample documents."""
    return len(get_sample_documents())

def get_documents_by_topic(topic: str) -> List[Dict[str, str]]:
    """
    Get documents filtered by topic.

    Args:
        topic: Topic to filter by

    Returns:
        List of documents matching the topic
    """
    all_docs = get_sample_documents()
    return [doc for doc in all_docs if doc["metadata"]["topic"] == topic]

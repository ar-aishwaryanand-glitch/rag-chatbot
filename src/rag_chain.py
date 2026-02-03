"""RAG chain implementation for question answering."""

from typing import List, Dict, Union, TYPE_CHECKING
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
import time

from .config import Config
from .observability import get_observability, instrumented

if TYPE_CHECKING:
    from .vector_store import VectorStoreManager
    from .document_manager import DocumentManager

class RAGChain:
    """Implements the RAG (Retrieval-Augmented Generation) chain."""

    def __init__(self, vector_store_manager: Union['VectorStoreManager', 'DocumentManager']):
        """
        Initialize the RAG chain.

        Args:
            vector_store_manager: Instance of VectorStoreManager or DocumentManager
        """
        self.vector_store_manager = vector_store_manager
        self.observability = get_observability()

        # Initialize LLM based on provider
        self.llm = self._initialize_llm()

        # Create prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant that answers questions based on the provided context.

Instructions:
- Use ONLY the information from the context below to answer the question
- If the context doesn't contain relevant information, say "I don't have enough information to answer this question based on the provided context."
- Be concise and clear in your answers
- If you use information from the context, mention which source it came from
- Do not make up information or use external knowledge

Context:
{context}"""),
            ("human", "{question}")
        ])

    def _initialize_llm(self):
        """Initialize the appropriate LLM based on configuration."""
        if Config.LLM_PROVIDER == "groq":
            try:
                from langchain_groq import ChatGroq
                print(f"🤖 Initializing Groq LLM: {Config.GROQ_MODEL}")
                return ChatGroq(
                    model=Config.GROQ_MODEL,
                    temperature=Config.LLM_TEMPERATURE,
                    max_tokens=Config.LLM_MAX_TOKENS,
                    groq_api_key=Config.GROQ_API_KEY
                )
            except ImportError as e:
                print(f"⚠️  Warning: Could not import langchain_groq: {e}")
                print("   Installing required packages...")
                import subprocess
                subprocess.run(["pip", "install", "langchain-groq", "-q"])
                from langchain_groq import ChatGroq
                return ChatGroq(
                    model=Config.GROQ_MODEL,
                    temperature=Config.LLM_TEMPERATURE,
                    max_tokens=Config.LLM_MAX_TOKENS,
                    groq_api_key=Config.GROQ_API_KEY
                )

        elif Config.LLM_PROVIDER == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            print(f"🤖 Initializing Google Gemini: {Config.GEMINI_MODEL}")
            return ChatGoogleGenerativeAI(
                model=Config.GEMINI_MODEL,
                temperature=Config.LLM_TEMPERATURE,
                max_output_tokens=Config.LLM_MAX_TOKENS,
                google_api_key=Config.GOOGLE_API_KEY
            )

        else:
            raise ValueError(
                f"Unsupported LLM provider: {Config.LLM_PROVIDER}. "
                "Supported providers: groq, google"
            )

    def retrieve_context(self, query: str, k: int = Config.TOP_K_RESULTS) -> List[Document]:
        """
        Retrieve relevant context for the query.

        Args:
            query: User question
            k: Number of chunks to retrieve

        Returns:
            List of relevant Document chunks
        """
        start_time = time.time()

        with self.observability.trace_operation(
            "retrieve_context",
            attributes={
                "query": query[:100],  # First 100 chars
                "top_k": k,
                "vector_store": Config.get_vector_store_display_name()
            }
        ) as span:
            results = self.vector_store_manager.similarity_search_with_score(query, k=k)

            # Extract documents (ignore scores for now)
            documents = [doc for doc, score in results]

            # Add span attributes
            if span:
                span.set_attribute("documents_retrieved", len(documents))
                if documents:
                    span.set_attribute("avg_score", sum(score for _, score in results) / len(results))

            # Record metric
            duration_ms = (time.time() - start_time) * 1000
            self.observability.record_metric(
                "retrieval",
                duration_ms,
                {"top_k": k, "num_results": len(documents)}
            )

            return documents

    def format_context(self, documents: List[Document]) -> str:
        """
        Format retrieved documents into context string.

        Args:
            documents: List of Document chunks

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "unknown")
            topic = doc.metadata.get("topic", "unknown")
            content = doc.page_content.strip()

            context_parts.append(
                f"[Source {i}: {source} (Topic: {topic})]\n{content}"
            )

        return "\n\n---\n\n".join(context_parts)

    def generate_answer(self, query: str, context: str) -> str:
        """
        Generate answer using the LLM.

        Args:
            query: User question
            context: Retrieved context

        Returns:
            Generated answer
        """
        start_time = time.time()

        with self.observability.trace_operation(
            "generate_answer",
            attributes={
                "query": query[:100],
                "context_length": len(context),
                "llm": Config.get_llm_display_name()
            }
        ) as span:
            # Format the prompt
            messages = self.prompt_template.format_messages(
                context=context,
                question=query
            )

            # Generate response
            response = self.llm.invoke(messages)

            # Add span attributes
            if span:
                span.set_attribute("answer_length", len(response.content))

            # Record metric
            duration_ms = (time.time() - start_time) * 1000
            self.observability.record_metric(
                "generation",
                duration_ms,
                {"llm": Config.LLM_PROVIDER}
            )

            return response.content

    def ask(self, question: str, top_k: int = None) -> Dict[str, any]:
        """
        Main RAG pipeline: retrieve context and generate answer.

        Args:
            question: User question
            top_k: Number of document chunks to retrieve (uses Config.TOP_K_RESULTS if not specified)

        Returns:
            Dictionary with answer, context, and metadata
        """
        start_time = time.time()

        # Use Config default if top_k not specified
        if top_k is None:
            top_k = Config.TOP_K_RESULTS

        with self.observability.trace_operation(
            "rag_query",
            attributes={
                "query": question[:100],
                "llm": Config.get_llm_display_name(),
                "vector_store": Config.get_vector_store_display_name(),
                "top_k": top_k
            }
        ) as span:
            try:
                print(f"\n🔍 Processing question: {question}")

                # Step 1: Retrieve relevant context
                print("📚 Retrieving relevant context...")
                documents = self.retrieve_context(question, k=top_k)

                if not documents:
                    if span:
                        span.set_attribute("no_context_found", True)
                    return {
                        "question": question,
                        "answer": "No relevant context found for your question.",
                        "context": [],
                        "sources": []
                    }

                # Step 2: Format context
                context = self.format_context(documents)

                # Step 3: Generate answer
                llm_name = Config.get_llm_display_name()
                print(f"🤖 Generating answer with {llm_name}...")
                answer = self.generate_answer(question, context)

                # Step 4: Extract sources
                sources = [
                    {
                        "source": doc.metadata.get("source", "unknown"),
                        "topic": doc.metadata.get("topic", "unknown"),
                        "content": doc.page_content.strip()[:200] + "..."  # First 200 chars
                    }
                    for doc in documents
                ]

                # Add span attributes
                if span:
                    span.set_attribute("num_sources", len(sources))
                    span.set_attribute("answer_length", len(answer))

                # Record overall query metric
                duration_ms = (time.time() - start_time) * 1000
                self.observability.record_metric(
                    "query",
                    duration_ms,
                    {
                        "llm": Config.LLM_PROVIDER,
                        "vector_store": "pinecone" if Config.USE_PINECONE else "faiss",
                        "num_sources": len(sources)
                    }
                )

                return {
                    "question": question,
                    "answer": answer,
                    "context": documents,
                    "sources": sources
                }

            except Exception as e:
                # Record error metric
                self.observability.record_metric(
                    "error",
                    0,
                    {"operation": "rag_query", "error": str(e)[:100]}
                )
                raise

    def display_result(self, result: Dict[str, any]) -> None:
        """
        Display the RAG result in a formatted way.

        Args:
            result: Result dictionary from ask()
        """
        print("\n" + "="*80)
        print(f"❓ Question: {result['question']}")
        print("="*80)

        print(f"\n💡 Answer:\n{result['answer']}")

        print(f"\n📖 Sources Used ({len(result['sources'])}):")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n  {i}. Source: {source['source']} (Topic: {source['topic']})")
            print(f"     Preview: {source['content']}")

        print("\n" + "="*80)

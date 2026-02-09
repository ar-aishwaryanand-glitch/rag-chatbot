"""RAG chain implementation for question answering."""

from typing import List, Dict, Union, TYPE_CHECKING, Tuple, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
import time

from .config import Config
from .observability import get_observability

if TYPE_CHECKING:
    from .vector_store import VectorStoreManager
    from .document_manager import DocumentManager

# Lazy load reranker to avoid import overhead
_reranker = None

def get_reranker():
    """Lazy load the cross-encoder reranker."""
    global _reranker
    if _reranker is None and Config.ENABLE_RERANKING:
        try:
            from sentence_transformers import CrossEncoder
            print(f"Loading reranker model: {Config.RERANK_MODEL}")
            _reranker = CrossEncoder(Config.RERANK_MODEL)
        except ImportError:
            print("Warning: sentence-transformers not installed. Reranking disabled.")
            print("Install with: pip install sentence-transformers")
    return _reranker

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
            ("system", """You are a knowledgeable AI assistant that provides thorough, educational answers based on the provided context.

Instructions:
- Provide a DETAILED and COMPREHENSIVE answer using the information from the context below
- Structure your answer with clear explanations, including:
  - Key concepts and definitions
  - How things work (architecture, mechanisms, processes)
  - Practical examples when available
  - Important details and nuances
- If the context contains technical information, explain it clearly
- Use paragraphs for readability, but use bullet points for lists of items when appropriate
- If the context doesn't contain enough information, say so, but still provide what's available
- After your main answer, add a "Sources:" section listing the documents you referenced
- Format sources as: "Sources: [Document Name 1], [Document Name 2]"

Context:
{context}"""),
            ("human", "{question}")
        ])

        # Test Case Generation prompt template
        self.test_case_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert QA Engineer specializing in test case design. Your task is to generate comprehensive test cases based on the requirements provided.

INSTRUCTIONS:
1. Analyze the requirements thoroughly
2. Generate test cases covering:
   - Positive/Happy path scenarios
   - Negative/Error scenarios
   - Edge cases and boundary conditions
   - Input validation
3. For each test case, provide:
   - Test Case ID (format: TC_XXX)
   - Title (brief description)
   - Priority (High/Medium/Low)
   - Type (Functional/Negative/Edge Case/Integration/UI)
   - Preconditions (setup required)
   - Test Steps in Given/When/Then format
   - Expected Result
   - Test Data (if applicable)

OUTPUT FORMAT:
For each test case, use this structure:

---
**TC_001: [Title]**
- **Priority:** High/Medium/Low
- **Type:** Functional/Negative/Edge Case
- **Preconditions:** [List any setup required]

**Steps:**
- **Given:** [Initial state/context]
- **When:** [Action performed]
- **Then:** [Expected outcome]

**Test Data:** [Any specific data needed]
---

IMPORTANT:
- Be thorough - cover all requirements mentioned
- Think about what could go wrong
- Include boundary value tests
- Consider user permissions if applicable
- Add data validation tests

Requirements Context:
{context}"""),
            ("human", "{question}")
        ])

        # Pytest Code Generation prompt template
        self.pytest_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert QA Engineer who writes pytest test code. Generate Python pytest skeleton code based on the requirements provided.

OUTPUT FORMAT:
Generate valid Python code with this structure:

```python
import pytest

class Test<FeatureName>:
    \"\"\"Test cases for <Feature> requirements\"\"\"

    @pytest.fixture
    def setup(self):
        \"\"\"Setup test fixtures\"\"\"
        # TODO: Add setup code
        pass

    @pytest.mark.priority_high
    def test_tc_001_<descriptive_name>(self):
        \"\"\"TC_001: <Title>

        Given: <Initial state/context>
        When: <Action performed>
        Then: <Expected outcome>
        \"\"\"
        # TODO: Implement test
        # Arrange

        # Act

        # Assert
        pass

    @pytest.mark.priority_medium
    @pytest.mark.negative
    def test_tc_002_<descriptive_name>(self):
        \"\"\"TC_002: <Title>\"\"\"
        # TODO: Implement test
        pass
```

RULES:
1. Use class-based test structure
2. Add pytest markers: @pytest.mark.priority_high, @pytest.mark.priority_medium, @pytest.mark.priority_low
3. Add type markers: @pytest.mark.functional, @pytest.mark.negative, @pytest.mark.edge_case, @pytest.mark.integration
4. Include docstrings with Given/When/Then format
5. Use descriptive test method names (test_tc_XXX_descriptive_name)
6. Add `pass` placeholder and TODO comments
7. Include a setup fixture if needed
8. Generate ONLY valid Python code - no markdown, no explanations outside of code
9. Start with `import pytest` and end with the last test method

Requirements Context:
{context}"""),
            ("human", "Generate pytest code for: {question}")
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

    def retrieve_context(
        self,
        query: str,
        k: int = Config.TOP_K_RESULTS,
        apply_reranking: bool = True,
        min_relevance: Optional[float] = None
    ) -> List[Document]:
        """
        Retrieve relevant context for the query with optional reranking and filtering.

        Args:
            query: User question
            k: Number of chunks to retrieve
            apply_reranking: Whether to apply cross-encoder reranking
            min_relevance: Minimum relevance score threshold (0-1). Uses Config.RELEVANCE_THRESHOLD if None.

        Returns:
            List of relevant Document chunks
        """
        start_time = time.time()
        min_relevance = min_relevance if min_relevance is not None else Config.RELEVANCE_THRESHOLD

        with self.observability.trace_operation(
            "retrieve_context",
            attributes={
                "query": query[:100],  # First 100 chars
                "top_k": k,
                "vector_store": Config.get_vector_store_display_name(),
                "reranking": apply_reranking,
                "min_relevance": min_relevance
            }
        ) as span:
            # Retrieve more candidates if reranking is enabled
            retrieve_k = k * 3 if apply_reranking and Config.ENABLE_RERANKING else k
            results = self.vector_store_manager.similarity_search_with_score(query, k=retrieve_k)

            # Step 1: Apply relevance threshold filtering
            if min_relevance > 0:
                # Note: FAISS returns distance (lower is better), convert to similarity
                filtered_results = []
                for doc, score in results:
                    # For FAISS, score is distance. Convert: similarity = 1 / (1 + distance)
                    # For cosine similarity in FAISS, lower distance = more similar
                    similarity = 1 / (1 + score) if score >= 0 else 0
                    if similarity >= min_relevance:
                        filtered_results.append((doc, score, similarity))

                if filtered_results:
                    results = [(doc, score) for doc, score, _ in filtered_results]
                    print(f"Relevance filter: {len(filtered_results)}/{retrieve_k} chunks passed threshold {min_relevance}")

            # Step 2: Apply reranking if enabled
            if apply_reranking and Config.ENABLE_RERANKING and len(results) > 0:
                reranker = get_reranker()
                if reranker is not None:
                    results = self._rerank_results(query, results, k, reranker)

            # Extract top k documents
            documents = [doc for doc, score in results[:k]]

            # Add span attributes
            if span:
                span.set_attribute("documents_retrieved", len(documents))
                span.set_attribute("candidates_before_filter", retrieve_k)
                if results:
                    span.set_attribute("avg_score", sum(score for _, score in results[:k]) / min(k, len(results)))

            # Record metric
            duration_ms = (time.time() - start_time) * 1000
            self.observability.record_metric(
                "retrieval",
                duration_ms,
                {"top_k": k, "num_results": len(documents), "reranked": apply_reranking}
            )

            return documents

    def _rerank_results(
        self,
        query: str,
        results: List[Tuple[Document, float]],
        k: int,
        reranker
    ) -> List[Tuple[Document, float]]:
        """
        Rerank results using cross-encoder model.

        Args:
            query: The search query
            results: List of (Document, score) tuples
            k: Number of results to return
            reranker: CrossEncoder model instance

        Returns:
            Reranked list of (Document, score) tuples
        """
        if not results:
            return results

        # Prepare query-document pairs for reranking
        pairs = [(query, doc.page_content) for doc, _ in results]

        # Get reranking scores
        rerank_scores = reranker.predict(pairs)

        # Combine with original results and sort by rerank score
        reranked = list(zip(results, rerank_scores))
        reranked.sort(key=lambda x: x[1], reverse=True)

        # Return top k with new scores
        return [(doc, float(rerank_score)) for (doc, _), rerank_score in reranked[:k]]

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

    def generate_test_cases(
        self,
        requirement_query: str,
        top_k: int = None
    ) -> Dict[str, any]:
        """
        Generate QA test cases from requirements.

        Uses specialized prompt template and retrieves more context for comprehensive coverage.

        Args:
            requirement_query: Query to find relevant requirements (e.g., "Client Setting Page requirements")
            top_k: Number of requirement chunks to retrieve (uses Config.TOP_K_REQUIREMENTS if not specified)

        Returns:
            Dictionary with test cases, context, and metadata
        """
        start_time = time.time()

        # Use higher retrieval count for requirements
        if top_k is None:
            top_k = Config.TOP_K_REQUIREMENTS

        with self.observability.trace_operation(
            "generate_test_cases",
            attributes={
                "query": requirement_query[:100],
                "llm": Config.get_llm_display_name(),
                "top_k": top_k
            }
        ) as span:
            try:
                print(f"\n🧪 Generating test cases for: {requirement_query}")

                # Step 1: Retrieve requirements with reranking for best relevance
                print("📚 Retrieving requirements context...")
                documents = self.retrieve_context(
                    requirement_query,
                    k=top_k,
                    apply_reranking=True,
                    min_relevance=Config.RELEVANCE_THRESHOLD
                )

                if not documents:
                    if span:
                        span.set_attribute("no_context_found", True)
                    return {
                        "query": requirement_query,
                        "test_cases": "No relevant requirements found. Please import requirements from Confluence first.",
                        "context": [],
                        "sources": [],
                        "num_requirements": 0
                    }

                # Step 2: Format context
                context = self.format_context(documents)

                # Step 3: Generate test cases using specialized prompt
                llm_name = Config.get_llm_display_name()
                print(f"🤖 Generating test cases with {llm_name}...")

                # Use test case prompt
                prompt = f"Generate comprehensive test cases for the following requirements. Be thorough and cover all scenarios:\n\n{requirement_query}"

                messages = self.test_case_prompt.format_messages(
                    context=context,
                    question=prompt
                )
                response = self.llm.invoke(messages)
                test_cases = response.content

                # Step 4: Extract sources
                sources = [
                    {
                        "source": doc.metadata.get("source", "unknown"),
                        "title": doc.metadata.get("title", "unknown"),
                        "topic": doc.metadata.get("topic", "unknown"),
                        "content": doc.page_content.strip()[:300] + "..."
                    }
                    for doc in documents
                ]

                # Add span attributes
                if span:
                    span.set_attribute("num_sources", len(sources))
                    span.set_attribute("test_cases_length", len(test_cases))

                # Record metric
                duration_ms = (time.time() - start_time) * 1000
                self.observability.record_metric(
                    "test_case_generation",
                    duration_ms,
                    {"num_requirements": len(documents)}
                )

                print(f"✅ Generated test cases from {len(documents)} requirement chunks")

                return {
                    "query": requirement_query,
                    "test_cases": test_cases,
                    "context": documents,
                    "sources": sources,
                    "num_requirements": len(documents)
                }

            except Exception as e:
                self.observability.record_metric(
                    "error",
                    0,
                    {"operation": "generate_test_cases", "error": str(e)[:100]}
                )
                raise

    def generate_pytest_code(
        self,
        requirement_query: str,
        top_k: int = None
    ) -> Dict[str, any]:
        """
        Generate pytest skeleton code from requirements.

        Uses specialized prompt template to generate valid Python test code.

        Args:
            requirement_query: Query to find relevant requirements
            top_k: Number of requirement chunks to retrieve

        Returns:
            Dictionary with pytest code, suggested filename, and metadata
        """
        start_time = time.time()

        if top_k is None:
            top_k = Config.TOP_K_REQUIREMENTS

        with self.observability.trace_operation(
            "generate_pytest_code",
            attributes={
                "query": requirement_query[:100],
                "llm": Config.get_llm_display_name(),
                "top_k": top_k
            }
        ) as span:
            try:
                print(f"\n🐍 Generating pytest code for: {requirement_query}")

                # Step 1: Retrieve requirements with reranking
                print("📚 Retrieving requirements context...")
                documents = self.retrieve_context(
                    requirement_query,
                    k=top_k,
                    apply_reranking=True,
                    min_relevance=Config.RELEVANCE_THRESHOLD
                )

                if not documents:
                    if span:
                        span.set_attribute("no_context_found", True)
                    return {
                        "query": requirement_query,
                        "pytest_code": "# No relevant requirements found.\n# Please import requirements from Confluence first.",
                        "suggested_filename": "test_placeholder.py",
                        "context": [],
                        "sources": [],
                        "num_requirements": 0
                    }

                # Step 2: Format context
                context = self.format_context(documents)

                # Step 3: Generate pytest code using specialized prompt
                llm_name = Config.get_llm_display_name()
                print(f"🤖 Generating pytest code with {llm_name}...")

                messages = self.pytest_prompt.format_messages(
                    context=context,
                    question=requirement_query
                )
                response = self.llm.invoke(messages)
                pytest_code = response.content

                # Clean up the code - remove markdown code blocks if present
                pytest_code = self._clean_code_output(pytest_code)

                # Generate suggested filename
                feature_name = self._extract_feature_name(requirement_query)
                suggested_filename = f"test_{feature_name}.py"

                # Step 4: Extract sources
                sources = [
                    {
                        "source": doc.metadata.get("source", "unknown"),
                        "title": doc.metadata.get("title", "unknown"),
                        "topic": doc.metadata.get("topic", "unknown"),
                    }
                    for doc in documents
                ]

                # Add span attributes
                if span:
                    span.set_attribute("num_sources", len(sources))
                    span.set_attribute("code_length", len(pytest_code))

                # Record metric
                duration_ms = (time.time() - start_time) * 1000
                self.observability.record_metric(
                    "pytest_code_generation",
                    duration_ms,
                    {"num_requirements": len(documents)}
                )

                print(f"✅ Generated pytest code from {len(documents)} requirement chunks")

                return {
                    "query": requirement_query,
                    "pytest_code": pytest_code,
                    "suggested_filename": suggested_filename,
                    "context": documents,
                    "sources": sources,
                    "num_requirements": len(documents)
                }

            except Exception as e:
                self.observability.record_metric(
                    "error",
                    0,
                    {"operation": "generate_pytest_code", "error": str(e)[:100]}
                )
                raise

    def _clean_code_output(self, code: str) -> str:
        """Remove markdown code blocks from LLM output."""
        import re
        # Remove ```python and ``` markers
        code = re.sub(r'^```python\s*\n?', '', code.strip())
        code = re.sub(r'\n?```\s*$', '', code)
        # Also handle generic code blocks
        code = re.sub(r'^```\s*\n?', '', code)
        return code.strip()

    def _extract_feature_name(self, query: str) -> str:
        """Extract a valid Python filename from the query."""
        import re
        # Extract key words, convert to snake_case
        words = re.findall(r'\b[a-zA-Z]+\b', query.lower())
        # Take first 3-4 meaningful words, skip common words
        skip_words = {'the', 'a', 'an', 'for', 'and', 'or', 'to', 'of', 'in', 'on', 'requirements', 'page'}
        feature_words = [w for w in words if w not in skip_words][:4]
        if not feature_words:
            feature_words = ['feature']
        return '_'.join(feature_words)

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

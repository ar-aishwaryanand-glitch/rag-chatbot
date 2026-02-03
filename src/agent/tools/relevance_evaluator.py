"""
Relevance Evaluator - Determines if content is relevant to a query.

Uses LLM to evaluate relevance of articles, web pages, or other content.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import os


@dataclass
class RelevanceResult:
    """Result of relevance evaluation."""
    is_relevant: bool
    confidence: float  # 0.0 to 1.0
    reason: str


class RelevanceEvaluator:
    """
    Evaluates content relevance using LLM.

    Features:
    - Binary relevance classification (relevant/not relevant)
    - Confidence scoring
    - Explanation generation
    - Batch evaluation support
    """

    def __init__(self, llm_client=None, threshold: float = 0.6):
        """
        Initialize relevance evaluator.

        Args:
            llm_client: Optional LLM client (Anthropic, OpenAI, etc.)
            threshold: Minimum confidence for considering content relevant (0.0-1.0)
        """
        self.llm_client = llm_client
        self.threshold = threshold

    def evaluate_article(
        self,
        query: str,
        title: str,
        description: str,
        use_llm: bool = True
    ) -> RelevanceResult:
        """
        Evaluate if an article is relevant to the query.

        Args:
            query: User's search query or topic
            title: Article title
            description: Article description/summary
            use_llm: Whether to use LLM evaluation (vs simple keyword matching)

        Returns:
            RelevanceResult with relevance determination
        """
        if use_llm and self.llm_client:
            return self._evaluate_with_llm(query, title, description)
        else:
            return self._evaluate_with_keywords(query, title, description)

    def _evaluate_with_llm(
        self,
        query: str,
        title: str,
        description: str
    ) -> RelevanceResult:
        """Evaluate relevance using LLM."""
        try:
            prompt = f"""Evaluate if this article is relevant to the user's query.

User Query: "{query}"

Article:
Title: {title}
Description: {description}

Is this article relevant to the user's query?

Respond in this exact format:
RELEVANT: yes/no
CONFIDENCE: 0.0-1.0 (how confident are you?)
REASON: brief explanation (one sentence)

Example:
RELEVANT: yes
CONFIDENCE: 0.9
REASON: Article directly discusses the topic mentioned in the query."""

            # Call LLM (support multiple client types)
            content = None

            # Try langchain-style LLM (has .invoke or .predict)
            if hasattr(self.llm_client, 'invoke'):
                # Langchain >= 0.1.0
                response = self.llm_client.invoke(prompt)
                content = str(response).strip()

            elif hasattr(self.llm_client, 'predict'):
                # Older langchain versions
                content = self.llm_client.predict(prompt).strip()

            # Try Anthropic client (has .messages.create)
            elif hasattr(self.llm_client, 'messages'):
                response = self.llm_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=150,
                    temperature=0.0,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                content = response.content[0].text.strip()

            # Try OpenAI-style client (has .chat.completions.create)
            elif hasattr(self.llm_client, 'chat'):
                response = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    max_tokens=150,
                    temperature=0.0,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                content = response.choices[0].message.content.strip()

            # Try as a generic callable
            elif callable(self.llm_client):
                content = str(self.llm_client(prompt)).strip()

            else:
                raise ValueError("Unsupported LLM client type")

            if not content:
                raise ValueError("Empty response from LLM")

            # Parse response
            lines = content.split('\n')

            relevant = False
            confidence = 0.5
            reason = "Unable to determine"

            for line in lines:
                line = line.strip()
                if line.startswith('RELEVANT:'):
                    relevant = 'yes' in line.lower()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.split(':')[1].strip())
                    except:
                        confidence = 0.5
                elif line.startswith('REASON:'):
                    reason = line.split(':', 1)[1].strip()

            return RelevanceResult(
                is_relevant=relevant and confidence >= self.threshold,
                confidence=confidence,
                reason=reason
            )

        except Exception as e:
            print(f"⚠️ LLM evaluation failed: {e}, falling back to keyword matching")
            return self._evaluate_with_keywords(query, title, description)

    def _evaluate_with_keywords(
        self,
        query: str,
        title: str,
        description: str
    ) -> RelevanceResult:
        """Fallback: Simple keyword-based relevance evaluation."""
        # Extract keywords from query
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Combine title and description
        content_lower = (title + " " + description).lower()
        content_words = set(content_lower.split())

        # Calculate overlap
        common_words = query_words.intersection(content_words)

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'about', 'is', 'are', 'was', 'were'}
        meaningful_common = common_words - stop_words

        # Calculate confidence based on overlap
        if len(query_words - stop_words) == 0:
            confidence = 0.5
        else:
            confidence = len(meaningful_common) / len(query_words - stop_words)

        is_relevant = confidence >= self.threshold

        if is_relevant:
            reason = f"Found {len(meaningful_common)} relevant keywords: {', '.join(list(meaningful_common)[:3])}"
        else:
            reason = f"Low keyword overlap ({confidence:.1%})"

        return RelevanceResult(
            is_relevant=is_relevant,
            confidence=confidence,
            reason=reason
        )

    def filter_articles(
        self,
        query: str,
        articles: List[Dict[str, Any]],
        use_llm: bool = True,
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of articles, keeping only relevant ones.

        Args:
            query: User's search query
            articles: List of article dictionaries with 'title' and 'description'
            use_llm: Whether to use LLM evaluation
            verbose: Whether to print filtering details

        Returns:
            Filtered list of relevant articles
        """
        relevant_articles = []

        for i, article in enumerate(articles):
            title = article.get('title', '')
            description = article.get('description', '')

            result = self.evaluate_article(query, title, description, use_llm)

            if verbose:
                status = "✓ RELEVANT" if result.is_relevant else "✗ NOT RELEVANT"
                print(f"{status} ({result.confidence:.2f}): {title[:60]}...")
                print(f"  Reason: {result.reason}")

            if result.is_relevant:
                # Add relevance metadata to article
                article['relevance_score'] = result.confidence
                article['relevance_reason'] = result.reason
                relevant_articles.append(article)

        return relevant_articles

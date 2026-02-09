"""QA Pipeline - Orchestrates automated QA workflow after document import."""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import re


class PipelineStage(Enum):
    """Pipeline execution stages."""
    EXTRACT_REQUIREMENTS = "extract_requirements"
    GENERATE_TEST_CASES = "generate_test_cases"
    ANALYZE_GAPS = "analyze_gaps"
    COMPLETE = "complete"


@dataclass
class PipelineResult:
    """Result from a single pipeline stage."""
    success: bool
    stage: PipelineStage
    data: Dict[str, Any]
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class QAPipelineState:
    """State tracking for the QA pipeline."""
    current_stage: PipelineStage = PipelineStage.EXTRACT_REQUIREMENTS
    requirements: List[Dict] = field(default_factory=list)
    requirements_text: str = ""
    test_cases: str = ""
    gap_analysis: str = ""
    errors: List[str] = field(default_factory=list)
    is_complete: bool = False
    progress_percent: int = 0


class QAPipeline:
    """
    Orchestrates the automated QA pipeline.

    Pipeline stages:
    1. Extract requirements from imported documents
    2. Generate test cases from requirements
    3. Analyze gaps in coverage

    Usage:
        pipeline = QAPipeline(rag_chain, req_tool, qa_tool, callback)
        results = pipeline.run("User Authentication")
    """

    def __init__(
        self,
        rag_chain,
        requirements_tool,
        qa_analysis_tool,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ):
        """
        Initialize the QA pipeline.

        Args:
            rag_chain: RAGChain instance for document access
            requirements_tool: RequirementsExtractorTool instance
            qa_analysis_tool: QAAnalysisTool instance
            progress_callback: Optional callback(message, percent) for progress updates
        """
        self.rag_chain = rag_chain
        self.requirements_tool = requirements_tool
        self.qa_analysis_tool = qa_analysis_tool
        self.progress_callback = progress_callback
        self.state = QAPipelineState()

    def _update_progress(self, message: str, percent: int):
        """Update progress via callback if provided."""
        self.state.progress_percent = percent
        if self.progress_callback:
            self.progress_callback(message, percent)

    def run(
        self,
        topic: str,
        document_filter: Optional[str] = None,
        skip_gaps: bool = False
    ) -> Dict[str, Any]:
        """
        Run the full QA pipeline.

        Args:
            topic: Topic/feature area to analyze
            document_filter: Optional filter for specific documents
            skip_gaps: Skip gap analysis stage

        Returns:
            Dictionary with all pipeline results
        """
        results = {
            "topic": topic,
            "stages": {},
            "success": False,
            "total_duration": 0.0
        }

        start_time = time.time()

        try:
            # Stage 1: Extract Requirements
            self._update_progress("Extracting requirements...", 10)
            req_result = self._extract_requirements(topic, document_filter)
            results["stages"]["requirements"] = {
                "success": req_result.success,
                "output": req_result.data.get("requirements", ""),
                "count": req_result.data.get("count", 0),
                "duration": req_result.duration,
                "error": req_result.error
            }

            if not req_result.success:
                results["error"] = f"Requirements extraction failed: {req_result.error}"
                return results

            self._update_progress("Requirements extracted", 33)

            # Stage 2: Generate Test Cases
            self._update_progress("Generating test cases...", 40)
            tc_result = self._generate_test_cases(topic)
            results["stages"]["test_cases"] = {
                "success": tc_result.success,
                "output": tc_result.data.get("test_cases", ""),
                "duration": tc_result.duration,
                "error": tc_result.error
            }

            if not tc_result.success:
                results["error"] = f"Test case generation failed: {tc_result.error}"
                return results

            self._update_progress("Test cases generated", 66)

            # Stage 3: Gap Analysis (optional)
            if not skip_gaps:
                self._update_progress("Analyzing coverage gaps...", 75)
                gap_result = self._analyze_gaps()
                results["stages"]["gap_analysis"] = {
                    "success": gap_result.success,
                    "output": gap_result.data.get("analysis", ""),
                    "duration": gap_result.duration,
                    "error": gap_result.error
                }

                if not gap_result.success:
                    results["error"] = f"Gap analysis failed: {gap_result.error}"
                    return results

            self._update_progress("Pipeline complete!", 100)
            results["success"] = True
            self.state.is_complete = True

        except Exception as e:
            results["error"] = str(e)
            self.state.errors.append(str(e))

        results["total_duration"] = time.time() - start_time
        return results

    def _extract_requirements(
        self,
        topic: str,
        document_filter: Optional[str]
    ) -> PipelineResult:
        """Stage 1: Extract requirements from documents."""
        start_time = time.time()

        try:
            result = self.requirements_tool.run(
                topic=topic,
                document_filter=document_filter,
                output_format="structured"
            )

            if result.success:
                self.state.requirements_text = result.output
                self.state.requirements = self._parse_requirements(result.output)
                self.state.current_stage = PipelineStage.GENERATE_TEST_CASES

            return PipelineResult(
                success=result.success,
                stage=PipelineStage.EXTRACT_REQUIREMENTS,
                data={
                    "requirements": result.output,
                    "count": len(self.state.requirements)
                },
                error=result.error,
                duration=time.time() - start_time
            )

        except Exception as e:
            return PipelineResult(
                success=False,
                stage=PipelineStage.EXTRACT_REQUIREMENTS,
                data={},
                error=str(e),
                duration=time.time() - start_time
            )

    def _generate_test_cases(self, topic: str) -> PipelineResult:
        """Stage 2: Generate test cases from requirements."""
        start_time = time.time()

        try:
            # Use RAG chain's test case generation
            result = self.rag_chain.generate_test_cases(
                requirement_query=topic,
                top_k=15
            )

            test_cases = result.get("test_cases", "")
            self.state.test_cases = test_cases
            self.state.current_stage = PipelineStage.ANALYZE_GAPS

            return PipelineResult(
                success=True,
                stage=PipelineStage.GENERATE_TEST_CASES,
                data={
                    "test_cases": test_cases,
                    "num_requirements": result.get("num_requirements", 0)
                },
                duration=time.time() - start_time
            )

        except Exception as e:
            return PipelineResult(
                success=False,
                stage=PipelineStage.GENERATE_TEST_CASES,
                data={},
                error=str(e),
                duration=time.time() - start_time
            )

    def _analyze_gaps(self) -> PipelineResult:
        """Stage 3: Analyze coverage gaps."""
        start_time = time.time()

        try:
            # Build requirements context for analysis
            req_context = "\n".join([
                f"{req.get('id', f'REQ-{i:03d}')}: {req.get('title', 'Untitled')}"
                for i, req in enumerate(self.state.requirements, 1)
            ])

            if not req_context:
                req_context = self.state.requirements_text[:2000]

            result = self.qa_analysis_tool.run(
                test_cases=self.state.test_cases,
                requirements=req_context
            )

            if result.success:
                self.state.gap_analysis = result.output
                self.state.current_stage = PipelineStage.COMPLETE

            return PipelineResult(
                success=result.success,
                stage=PipelineStage.ANALYZE_GAPS,
                data={"analysis": result.output},
                error=result.error,
                duration=time.time() - start_time
            )

        except Exception as e:
            return PipelineResult(
                success=False,
                stage=PipelineStage.ANALYZE_GAPS,
                data={},
                error=str(e),
                duration=time.time() - start_time
            )

    def _parse_requirements(self, requirements_text: str) -> List[Dict]:
        """Parse requirements text into structured list."""
        requirements = []

        # Parse REQ-XXX patterns
        pattern = r'###\s*(REQ-\d+):\s*(.+?)(?=###\s*REQ-|\Z)'
        matches = re.findall(pattern, requirements_text, re.DOTALL)

        for req_id, content in matches:
            lines = content.strip().split('\n')
            title = lines[0].strip() if lines else "Untitled"
            requirements.append({
                "id": req_id,
                "title": title,
                "content": content.strip()
            })

        # If no REQ-XXX found, try simpler patterns
        if not requirements:
            # Look for numbered requirements
            pattern = r'(\d+)\.\s*\*\*([^*]+)\*\*'
            matches = re.findall(pattern, requirements_text)
            for num, title in matches:
                requirements.append({
                    "id": f"REQ-{int(num):03d}",
                    "title": title.strip(),
                    "content": ""
                })

        return requirements

    def get_state(self) -> QAPipelineState:
        """Get current pipeline state."""
        return self.state

    def reset(self):
        """Reset pipeline state for new run."""
        self.state = QAPipelineState()

    def get_summary(self) -> str:
        """Get a summary of pipeline results."""
        if not self.state.is_complete:
            return f"Pipeline in progress: {self.state.current_stage.value} ({self.state.progress_percent}%)"

        return f"""## QA Pipeline Summary

**Requirements Extracted:** {len(self.state.requirements)}
**Test Cases Generated:** {'Yes' if self.state.test_cases else 'No'}
**Gap Analysis:** {'Complete' if self.state.gap_analysis else 'Skipped'}

### Quick Stats
- Stage: {self.state.current_stage.value}
- Errors: {len(self.state.errors)}
"""

# Codebase Concerns

**Analysis Date:** 2026-02-09

## Tech Debt

**Incomplete Document Indexing Implementation:**
- Issue: Document indexing in task queue is stubbed with `TODO` comment and `pass` statements
- Files: `src/task_queue/worker.py:237`
- Impact: Task queue cannot process `DOCUMENT_INDEX` tasks - they return mock results without actually indexing documents. Async document processing relies on placeholder implementation.
- Fix approach: Complete `_handle_document_index()` method to call document manager's indexing pipeline. Add integration tests to verify document processing through queue.

**Scattered Placeholder Methods:**
- Issue: 27+ methods across codebase contain `pass` statements without implementation
- Files: `src/rag_chain.py:136,152,159`, `src/ui/streamlit_app_agent.py:1656,1896`, `src/agent/tools/base_tool.py:36,42,52`, and others
- Impact: Abstract base classes and utility functions lack concrete implementations. Test framework methods are partially stubbed. Callers may not know which methods are unimplemented.
- Fix approach: Document which methods are intentional abstract methods vs. incomplete. Implement or remove placeholder methods. Add proper abstract base class decorators where appropriate.

**RAG Chain Test Case Generation (Lines 135-168):**
- Issue: Test case generation prompt and template parsing is outlined but helper methods are empty
- Files: `src/rag_chain.py:135-168`
- Impact: Callers cannot generate structured test cases from requirements; returns None silently. QA pipeline partially depends on this for test case synthesis.
- Fix approach: Implement `parse_test_cases()` and `generate_test_cases()` methods to extract test case structure from LLM responses using regex/parsing.

## Known Bugs

**Pickle Deserialization Security Risk:**
- Symptoms: Untrusted pickle data loaded without validation can execute arbitrary code during deserialization
- Files: `src/agent/reflection/learning_module.py:59`, `data/learning/learning_data.pkl`
- Trigger: Corrupt, malicious, or version-mismatched pickle file causes silent failure or code execution
- Workaround: Always validate pickle file integrity and never accept pickle files from untrusted sources. Restrict file permissions to `0600`.
- Root cause: Using pickle for persistence without validation or version pinning

**FAISS Deserialization Dangerous Flag:**
- Symptoms: `allow_dangerous_deserialization=True` flag bypasses safety checks on vector store loading
- Files: `src/vector_store.py:32,116`
- Trigger: Corrupt or malicious FAISS index file causes undefined behavior
- Workaround: Only load FAISS indices from trusted sources. Use file integrity checking (SHA256) before loading.
- Root cause: FAISS security flag required for backwards compatibility but introduces risk

**Unvalidated Document Index State:**
- Symptoms: Document auto-indexing may not track state correctly after app restart
- Files: `src/auto_indexer.py`, `src/ui/auto_index_integration.py`
- Trigger: App restart, concurrent uploads, network interruption during indexing
- Workaround: Manually re-index documents from UI if state appears inconsistent
- Root cause: Episodic memory stores index metadata in JSON but lacks atomic transactions

## Security Considerations

**Code Execution Tool Has Basic Sandboxing:**
- Risk: Even with AST validation and restricted builtins, malicious code may escape sandbox through Python interpreter vulnerabilities
- Files: `src/agent/tools/code_executor_tool.py:29-150`
- Current mitigation: Disabled by default (`CODE_EXECUTOR_ENABLED=false`), timeout enforcement, restricted `__builtins__`, AST validation before execution
- Recommendations: For production use, isolate execution in Docker container or subprocess with resource limits. Consider using RestrictedPython library. Add comprehensive input sanitization. Never enable without explicit user opt-in and warning.

**Confluence API Credentials in Environment:**
- Risk: API tokens and credentials stored in plaintext in `.env` file can be leaked if committed to git
- Files: `src/confluence_loader.py:39-64`, `.env`
- Current mitigation: `.env` is in `.gitignore`, credentials loaded via `Config.CONFLUENCE_*` variables
- Recommendations: Use secrets manager (AWS Secrets, HashiCorp Vault, Supabase) instead of `.env` for production. Implement credential rotation policy. Audit all `.gitignore` violations regularly. Use environment-specific credential scoping.

**Database Connection Pooling Threads:**
- Risk: ThreadPoolExecutor with 3 workers in `PostgresBackend` may cause resource exhaustion under high load or thread leaks on application crash
- Files: `src/database/postgres_backend.py:49`
- Current mitigation: Executor defined with max_workers=3, connection pool size 3-20
- Recommendations: Use context managers for all database operations to ensure cleanup. Implement executor shutdown on application exit (atexit hook). Monitor thread count in production. Consider using async/await instead of threads for I/O.

**Missing Rate Limiting on Tool Execution:**
- Risk: No rate limits on expensive tools (web agent, code executor) allows DoS or cost explosion from single session
- Files: `src/agent/agent_executor_v3.py:266-450` (tool execution), `src/policy/policy_engine.py` (incomplete integration)
- Current mitigation: Policy engine has rate limit definitions but not enforced in tool execution loop
- Recommendations: Implement rate limit checks before tool execution. Track tool costs and implement budget alerts. Add per-session and per-tool quotas. Implement exponential backoff for retries.

**Web Scraping Tool Insufficient User-Agent & Error Handling:**
- Risk: Playwright-based web agent may get blocked by WAF/anti-bot systems or scrape harmful content without validation
- Files: `src/agent/tools/web_agent_tool.py:653` (incomplete error handling)
- Current mitigation: Basic Playwright setup, try-catch blocks around navigation
- Recommendations: Add realistic user-agent rotation, respect robots.txt, implement content filtering for malicious sites. Add retry logic with exponential backoff. Monitor for WAF blocks and gracefully degrade.

**No Input Validation on File Operations:**
- Risk: File paths from user input not validated can allow path traversal attacks (reading arbitrary files)
- Files: `src/agent/tools/file_ops_tool.py`, `src/ui/document_handler.py`
- Current mitigation: Workspace limited to `data/workspace/` directory
- Recommendations: Validate all file paths are within workspace boundary using `os.path.realpath()`. Reject paths containing `..` or symlinks. Implement allowlist of readable file types. Log all file access attempts.

**PostgreSQL Connection String Hardcoded Fallback:**
- Risk: Default credentials (`postgres:postgres@localhost:5432/rag_chatbot`) used if environment not configured, exposing database to unauthorized access
- Files: `src/database/postgres_backend.py:52-67`
- Current mitigation: Environment variables checked first, fallback only if missing
- Recommendations: Require explicit environment configuration for production deployments. Fail fast with clear error if credentials not provided. Never use default credentials. Validate connection before proceeding.

## Performance Bottlenecks

**Large Monolithic UI File (2446 lines):**
- Problem: `src/ui/streamlit_app_agent.py` is 2446 lines, making it difficult to test, modify, and reason about
- Files: `src/ui/streamlit_app_agent.py`
- Cause: All UI logic (chat, document upload, QA pipeline, manager agent, settings) combined in single file. Complex state management, multiple tabs/modes, extensive conditional rendering
- Improvement path: Split into feature modules: `chat_interface.py`, `document_upload.py`, `qa_dashboard.py`, `manager_mode.py`. Use composition pattern for UI components. Move business logic to dedicated service layer. Consider component-based architecture.

**Vector Store Batch Processing with Sleep Delay:**
- Problem: Creating FAISS index processes in small batches (size=3) with 2-second delays between batches - linear scaling for large document sets
- Files: `src/vector_store.py:39-82`
- Cause: Rate limiting to avoid embedding API overload, but delays are hardcoded and not tunable per embedding provider
- Improvement path: Move batch processing to async queue worker. Make batch size and delay configurable per embedding model. Implement exponential backoff only on actual rate limit errors. Profile embedding latency to set optimal batch size.

**Memory Context Built Repeatedly:**
- Problem: In agent executor, memory context is retrieved and formatted for every tool routing decision, even if conversation hasn't changed
- Files: `src/agent/agent_executor_v3.py:200-235`
- Cause: State management doesn't cache memory context; rebuilds formatting on each iteration
- Improvement path: Cache formatted memory context in state and update only when conversation memory changes. Use hash-based invalidation. Implement LRU cache for frequently accessed contexts.

**Task Queue Polling with Fixed Interval:**
- Problem: Workers poll Redis queue with fixed 1-second interval regardless of queue depth, wasting CPU when queue is empty
- Files: `src/task_queue/worker.py:80-150`
- Cause: Simple polling loop without exponential backoff
- Improvement path: Implement adaptive polling: check queue every 100ms when backlogged, 5s when empty. Use Redis BLPOP for blocking pop instead of polling. Add queue depth metrics.

**Reflection Module Writes All Data to Disk on Every Update:**
- Problem: `LearningModule._save_data()` serializes entire learning state (tool metrics, patterns, errors) with every reflection, creating I/O overhead
- Files: `src/agent/reflection/learning_module.py:88-105`
- Cause: No batching or debouncing of writes
- Improvement path: Batch writes - flush to disk every N reflections or every T seconds. Use append-only log for write amplification reduction. Consider in-memory cache with periodic sync. Add write rate limiting.

## Fragile Areas

**Memory Persistence Across Multiple Storage Backends:**
- Files: `src/agent/memory/`, `src/database/postgres_backend.py`, `data/` directories
- Why fragile: Conversation memory stored in JSON (episodic), checkpoint recovery in PostgreSQL, learning data in pickle. Different backends can get out of sync if app crashes during write. No transaction boundaries across stores.
- Safe modification: Always modify episodic memory and checkpoint data together in same transaction. Add state version numbers to detect inconsistencies. Test backup/restore scenarios. Document data flow between stores.
- Test coverage: Missing integration tests for multi-store consistency. No chaos tests for power failure during writes.

**Policy Engine Integration with Tool Execution:**
- Files: `src/agent/agent_executor_v3.py:282-311`, `src/policy/policy_engine.py`
- Why fragile: Policy decisions embedded in tool execution loop. If policy check fails, continues execution (fail-open). No audit trail of policy violations. Policies stored in YAML but not validated at startup.
- Safe modification: Wrap policy evaluation in try-catch with proper logging. Fail-closed for critical policies (code execution). Add policy schema validation. Test policy evaluation doesn't deadlock or timeout.
- Test coverage: Limited coverage of policy violation scenarios. Missing tests for edge cases (missing policies, malformed rules).

**Web Agent Playwright Browser Lifecycle:**
- Files: `src/agent/tools/web_agent_tool.py:150-250`
- Why fragile: Single browser instance shared across concurrent tool executions. No timeout enforcement per page load. Memory leak if pages not closed properly. Network errors during navigation can leave browser in bad state.
- Safe modification: Use browser pool with page lifecycle management. Set page load timeout explicitly. Implement page close/reset in finally blocks. Add browser health checks.
- Test coverage: No tests for concurrent access. Missing tests for network failures and timeout scenarios.

**Confluence API Integration with Pagination:**
- Files: `src/confluence_loader.py:100-200`
- Why fragile: Pagination not fully implemented for large spaces (>1000 pages). Network timeouts during multi-page fetch leave loader in inconsistent state. No retry logic for transient API errors.
- Safe modification: Implement full pagination with offset tracking. Add exponential backoff for API errors. Store checkpoint of last fetched page for resumability. Validate API responses before processing.
- Test coverage: No tests with large page counts. Missing tests for API rate limits and authentication failures.

**Auto Indexer Document Deduplication:**
- Files: `src/auto_indexer.py`, `src/document_manager.py`
- Why fragile: New documents checked against existing only by filename, not content. Identical documents re-indexed wasting compute. Index metadata stored in JSON episodic memory without consistency checks.
- Safe modification: Add content-based deduplication (hash of file content). Store document version info with checksums. Implement idempotent indexing operations. Add validation that index metadata matches actual vector store.
- Test coverage: No tests for duplicate document handling. Missing tests for index recovery after corruption.

## Scaling Limits

**FAISS In-Memory Vector Store:**
- Current capacity: ~100k documents (depends on embedding dimension and available RAM). Production uses 384-dim embeddings, ~1.5GB per 100k documents
- Limit: App crashes or becomes unresponsive when loading >500k documents into memory
- Scaling path: Migrate to Pinecone (already supported via `USE_PINECONE=true`). Add sharding logic if keeping FAISS. Implement periodic archive/purge of old documents. Monitor memory usage with alerting.

**PostgreSQL Connection Pool (3-20 connections):**
- Current capacity: ~20 concurrent database operations before queue buildup
- Limit: Connection exhaustion causes stalled queries and timeouts under heavy load
- Scaling path: Increase pool size based on load testing. Implement read replicas for read-heavy workloads. Use connection pooling proxy (PgBouncer). Monitor pool utilization metrics.

**Redis Task Queue Single Instance:**
- Current capacity: Handles ~100 tasks/second on moderate hardware
- Limit: Single Redis instance becomes bottleneck; no replication or failover
- Scaling path: Implement Redis cluster or Sentinel for high availability. Use Redis Streams for more reliable message delivery. Consider message broker alternative (RabbitMQ, AWS SQS) for enterprise deployments.

**LLM Token Budget (2048 max tokens):**
- Current capacity: ~1500 tokens for response in 4k context window
- Limit: Large documents or long conversations exceed budget, causing truncation
- Scaling path: Implement prompt compression (summarize old messages). Use longer context models (e.g., 32k models). Implement adaptive token budgets per query type. Archive old conversations.

## Dependencies at Risk

**Playwright (Web Scraping):**
- Risk: Playwright 1.x may have breaking API changes in 2.x. Browser binary compatibility issues across platforms.
- Impact: Web agent stops working if Playwright major version required. Browser crashes during updates.
- Migration plan: Pin Playwright to v1.x with explicit version. Test browser compatibility in CI across macOS/Linux/Windows. Implement fallback to requests/BeautifulSoup for simple HTML scraping.

**FAISS (Vector Store):**
- Risk: FAISS library sometimes incompatible with newer NumPy/PyTorch versions. Performance regressions in updates.
- Impact: Vector store fails to load or becomes slow after dependency updates. Migration effort if switching vector stores.
- Migration plan: Already have Pinecone as alternative via `USE_PINECONE`. Document FAISS compatibility matrix. Pin FAISS version and test updates before deploying.

**LangChain (Agent Framework):**
- Risk: LangChain API evolving rapidly; frequent deprecations. Custom tool integration may break between versions.
- Impact: Tools stop working after LangChain update. Tool API contract changes require code rewrites.
- Migration plan: Pin LangChain to stable 0.1.x. Monitor changelog for breaking changes. Implement abstraction layer for LangChain calls (LangGraphAdapter pattern). Have fallback to pure OpenAI SDK.

**Psycopg2 (PostgreSQL Driver):**
- Risk: Python 3.14+ may deprecate certain standard library features psycopg2 depends on.
- Impact: Database connection failures on newer Python versions.
- Migration plan: Migrate to psycopg 3.x (actively maintained). Test against Python 3.13+ regularly. Have SQLAlchemy as abstraction layer.

## Missing Critical Features

**No Authentication/Authorization Layer:**
- Problem: No user login, sessions are identified by connection only. Any two browser tabs share session state.
- Blocks: Multi-user deployments, audit trails, role-based feature access (admin vs. user), billing/usage tracking per user

**No Conversation Persistence UI:**
- Problem: Conversations lost on page refresh; no way to save, share, or restore previous chats
- Blocks: Enterprise use cases requiring conversation history, compliance auditing, team collaboration

**No Document Versioning/Audit Trail:**
- Problem: Documents replaced without tracking what changed, who changed it, when
- Blocks: Regulatory compliance, troubleshooting stale data, reverting bad document updates

**No Real-Time Collaboration:**
- Problem: Only single user can interact with agent at once; no multi-user workspace
- Blocks: Team QA planning, shared document review, real-time feedback

## Test Coverage Gaps

**Agent Tool Execution under Failure Conditions:**
- What's not tested: Network timeouts, API rate limits, partial tool failures (e.g., web agent gets 404)
- Files: `src/agent/agent_executor_v3.py:266-450`, `src/agent/tools/`
- Risk: Silent failures, infinite retries, or undefined behavior when tools fail. Agent gets stuck in error state.
- Priority: High - tool failures are common in production

**Memory System Consistency Across Crashes:**
- What's not tested: Data integrity after app crash during write to PostgreSQL, episodic memory JSON, or learning pickle
- Files: `src/agent/memory/`, `src/database/postgres_backend.py`, `src/agent/reflection/learning_module.py`
- Risk: Orphaned data, duplicate episodes, learning data corruption. Memory state becomes unusable.
- Priority: High - affects reliability in production

**Policy Engine Enforcement:**
- What's not tested: Policy violations are detected but not always enforced (fail-open default). Edge cases like policy file missing or malformed.
- Files: `src/policy/policy_engine.py`, `src/agent/agent_executor_v3.py:282-311`
- Risk: Dangerous tools (code executor) executed when policy engine fails. No audit of decisions.
- Priority: Critical for security-sensitive deployments

**Document Auto-Indexing Edge Cases:**
- What's not tested: Concurrent uploads of same document, uploading corrupted PDFs, network failure mid-upload, storage full conditions
- Files: `src/auto_indexer.py`, `src/ui/auto_index_integration.py`
- Risk: Partial indexing, duplicate documents, stalled indexing tasks, confusing error messages
- Priority: Medium - affects user experience on upload

**Confluence Loader with Large Spaces:**
- What's not tested: Spaces with 1000+ pages, API rate limiting during fetch, network interruption during pagination
- Files: `src/confluence_loader.py`
- Risk: Loader hangs or times out. Partial document set imported. No clear error message.
- Priority: Medium - blocks enterprise integrations

**Multi-Agent Orchestration Failure:**
- What's not tested: Manager agent when specialized agents fail, task scheduler with deadlocks, memory consistency across agents
- Files: `src/agent/manager_agent.py`, `src/agent/task_scheduler.py`, `src/agent/manager_memory.py`
- Risk: Manager agent hangs, agents enter deadlock, tasks dropped silently
- Priority: High - critical flow for QA automation

---

*Concerns audit: 2026-02-09*

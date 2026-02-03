# Tool Edge Cases and Security Analysis

**Generated:** 2026-02-03
**Status:** Critical issues found requiring immediate fixes

---

## 🔴 CRITICAL ISSUES (Require Immediate Fix)

### 1. CodeExecutorTool - Insufficient Sandboxing
**File:** [src/agent/tools/code_executor_tool.py](src/agent/tools/code_executor_tool.py)

**Severity:** CRITICAL - Remote Code Execution Risk

**Issues:**
- **Line 112:** Uses `exec()` directly without true sandboxing
- **Line 38-50:** Timeout parameter is accepted but NEVER enforced
- **Lines 140-158:** Security checks are easily bypassed:
  - Can use `__import__('os')` to bypass import checks
  - Can use `getattr(__builtins__, 'open')` to access blocked functions
  - Can use string concatenation to hide keywords
- **No resource limits:** No memory, CPU, or output size limits
- **Restricted __builtins__ insufficient:** Many escape vectors exist in Python

**Recommended Fixes:**
```python
# 1. Add timeout enforcement using signal or threading
# 2. Use subprocess isolation instead of exec()
# 3. Add AST parsing to detect dangerous patterns
# 4. Add memory and CPU limits (resource module on Unix)
# 5. Add output size limits
# 6. Consider using docker containers for true isolation
```

### 2. RAGTool - Unused Parameter and Missing Error Handling
**File:** [src/agent/tools/rag_tool.py](src/agent/tools/rag_tool.py)

**Severity:** HIGH - Functionality Bug

**Issues:**
- **Line 39:** `top_k` parameter is accepted but never used (not passed to `ask()`)
- **Line 51:** No error handling if `rag_chain.ask()` raises exception
- **Lines 61-66:** Assumes all sources have 'source', 'topic', 'content' keys - will crash with KeyError if missing

**Fix Required:** Use top_k parameter and add error handling

---

## 🟡 HIGH PRIORITY ISSUES

### 3. WebAgentTool - URL Validation Missing
**File:** [src/agent/tools/web_agent_tool.py](src/agent/tools/web_agent_tool.py)

**Severity:** HIGH - SSRF (Server-Side Request Forgery) Risk

**Issues:**
- **No URL validation:** Tool will attempt to visit ANY URL including:
  - `file:///etc/passwd` (local file access)
  - `http://localhost:8080` (internal services)
  - `http://169.254.169.254` (AWS metadata)
  - `javascript:alert(1)` (XSS-style)
- **Line 347:** Fixed 1000ms wait may be insufficient for slow sites
- **Line 437:** Filters lines < 20 chars - might remove important content (headers, list items)
- **Lines 293-353:** Browser resources not cleaned up in all error paths

**Recommended Fixes:**
- Add URL whitelist/blacklist validation
- Block private IP ranges (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Block file:// and javascript: schemes
- Add configurable wait time instead of hardcoded 1000ms
- Use try/finally to ensure browser cleanup

### 4. FileOpsTool - Limited Error Handling
**File:** [src/agent/tools/file_ops_tool.py](src/agent/tools/file_ops_tool.py)

**Severity:** MEDIUM

**Issues:**
- **Line 98:** Only tries UTF-8 encoding - fails on other encodings (ISO-8859-1, etc.)
- **Line 89-109:** No handling for permission errors in `_read_file` (only in `_list_directory`)
- **No handling for broken symlinks** - will raise exception
- **Line 146:** Search pattern not sanitized - special glob characters could cause issues
- **Line 40:** Operation parameter not validated for empty string

**Recommended Fixes:**
- Try multiple encodings (utf-8, latin-1, cp1252)
- Add permission error handling to _read_file
- Check if path is symlink and handle broken links
- Escape glob special characters in search pattern
- Validate operation parameter is non-empty

### 5. WebSearchTool - Missing Input Validation
**File:** [src/agent/tools/web_search_tool.py](src/agent/tools/web_search_tool.py)

**Severity:** MEDIUM

**Issues:**
- **Line 35:** No validation that query is non-empty
- **No rate limiting** - could spam DuckDuckGo and get IP banned
- **No timeout handling** - network requests could hang
- **No max query length** - extremely long queries could cause issues

**Recommended Fixes:**
- Validate query is non-empty and reasonable length (< 500 chars)
- Add rate limiting (e.g., max 10 requests per minute)
- Add timeout to DDGS calls
- Add retry logic with exponential backoff

---

## 🟢 LOW PRIORITY ISSUES

### 6. DocumentManagementTool - Performance Issues
**File:** [src/agent/tools/doc_management_tool.py](src/agent/tools/doc_management_tool.py)

**Severity:** LOW

**Issues:**
- **Line 121:** Queries with empty string to get sample docs - could be slow
- **Line 121:** Hardcoded k=100 - retrieves 100 documents every time
- **No caching** - repeatedly calls expensive operations

**Recommended Fixes:**
- Cache document list
- Reduce k value or make it configurable
- Use more efficient method to list documents if available

### 7. CalculatorTool - Already Fixed ✅
**File:** [src/agent/tools/calculator_tool.py](src/agent/tools/calculator_tool.py)

**Status:** Fixed in previous commit

**Previous Issue:** LLM was generating Unicode math symbols (√) instead of Python functions
**Fix Applied:** Improved prompt to explicitly request Python syntax

---

## Summary by Tool

| Tool | Critical | High | Medium | Low | Status |
|------|----------|------|--------|-----|--------|
| CodeExecutorTool | 1 | 0 | 0 | 0 | ⚠️ URGENT |
| RAGTool | 0 | 1 | 0 | 0 | ⚠️ Fix Required |
| WebAgentTool | 0 | 1 | 0 | 0 | ⚠️ Fix Required |
| FileOpsTool | 0 | 0 | 1 | 0 | ⚡ Should Fix |
| WebSearchTool | 0 | 0 | 1 | 0 | ⚡ Should Fix |
| DocumentManagementTool | 0 | 0 | 0 | 1 | ℹ️ Nice to Have |
| CalculatorTool | 0 | 0 | 0 | 0 | ✅ Fixed |

**Total Issues:** 2 Critical, 2 High, 2 Medium, 1 Low

---

## Recommended Action Plan

1. **Immediate (Critical):**
   - Fix CodeExecutorTool sandboxing and timeout enforcement
   - Fix RAGTool parameter usage and error handling

2. **High Priority (This Week):**
   - Add URL validation to WebAgentTool
   - Improve FileOpsTool error handling

3. **Medium Priority (This Sprint):**
   - Add input validation to WebSearchTool
   - Add rate limiting

4. **Low Priority (Backlog):**
   - Optimize DocumentManagementTool caching

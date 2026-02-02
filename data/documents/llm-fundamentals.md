# Large Language Models (LLMs) - Fundamentals

## Introduction to LLMs

Large Language Models are neural networks trained on vast amounts of text data to understand and generate human-like text. They power modern AI applications from chatbots to code assistants.

## Architecture

### Transformer Architecture
- **Self-Attention Mechanism**: Models relationships between all words
- **Multi-Head Attention**: Parallel attention for different aspects
- **Feed-Forward Networks**: Process attention outputs
- **Positional Encoding**: Maintains word order information

### Key Components
1. **Tokenizer**: Converts text to tokens (sub-word units)
2. **Embedding Layer**: Maps tokens to vectors
3. **Transformer Blocks**: Core processing (12-96+ layers)
4. **Output Layer**: Generates next token probabilities

## Major LLM Families

### OpenAI GPT Series
- **GPT-4**: Most capable, multimodal
- **GPT-4 Turbo**: Faster, cheaper, 128K context
- **GPT-3.5**: Fast, cost-effective for many tasks

### Anthropic Claude
- **Claude 3.5 Sonnet**: Balanced performance
- **Claude 3 Opus**: Highest capability
- **Claude 3 Haiku**: Fast, economical

### Meta Llama
- **Llama 3.3 70B**: Open source, highly capable
- **Llama 3.1 405B**: Massive scale
- **Llama 3.1 8B**: Efficient, runs locally

### Google Gemini
- **Gemini Ultra**: Most capable
- **Gemini Pro**: General purpose
- **Gemini Nano**: On-device

### Mistral AI
- **Mixtral 8x7B**: Mixture of Experts architecture
- **Mistral 7B**: High performance, efficient

## Key Concepts

### Context Window
- Amount of text the model can process at once
- Ranges from 4K to 1M+ tokens
- Longer context = more expensive

### Temperature
- Controls randomness (0.0 to 1.0+)
- Low (0.0-0.3): Deterministic, focused
- Medium (0.4-0.7): Balanced
- High (0.8-1.0+): Creative, varied

### Top-P (Nucleus Sampling)
- Alternative to temperature
- Samples from smallest set of tokens with cumulative probability P
- 0.9 = consider tokens making up top 90% probability

### Tokens
- Sub-word units (not words!)
- English: ~1 token = 0.75 words
- 1K tokens ≈ 750 words
- Price typically per million tokens

## Prompting Techniques

### Zero-Shot
```
Task: Translate to French
Input: Hello, how are you?
```

### Few-Shot
```
Task: Sentiment analysis
Input: "Great product!" → Positive
Input: "Terrible service" → Negative
Input: "It's okay" → ?
```

### Chain-of-Thought (CoT)
```
Question: Roger has 5 tennis balls. He buys 2 more cans of 3 balls each.
How many balls does he have?

Let's think step by step:
1. Roger starts with 5 balls
2. He buys 2 cans of 3 balls each = 2 * 3 = 6 balls
3. Total = 5 + 6 = 11 balls
```

### ReAct (Reason + Act)
```
Thought: I need to find the population of Tokyo
Action: search("Tokyo population 2024")
Observation: 37 million
Thought: Now I have the answer
Answer: Tokyo has approximately 37 million people
```

### System Prompts
- Set behavior and personality
- Define role and constraints
- Establish output format

## LLM Capabilities

### Text Generation
- Creative writing
- Code generation
- Email composition
- Content creation

### Analysis
- Sentiment analysis
- Text classification
- Entity extraction
- Summarization

### Reasoning
- Mathematical problem solving
- Logical deduction
- Planning and strategy

### Coding
- Code completion
- Bug fixing
- Code explanation
- Test generation

### Multimodal (GPT-4V, Claude, Gemini)
- Image understanding
- Vision + text reasoning
- Document analysis

## Limitations

1. **Knowledge Cutoff**: Training data has end date
2. **Hallucinations**: Can confidently state false information
3. **Reasoning Errors**: Struggles with complex logic
4. **Context Limits**: Can't process infinite text
5. **Bias**: Reflects biases in training data
6. **Lack of Real-Time Data**: No internet access (without tools)

## Inference Optimization

### Model Selection
- Choose smallest model that works
- GPT-3.5 vs GPT-4 is 10x cost difference

### Caching
- Cache system prompts (Claude, OpenAI)
- Reuse context when possible

### Batch Processing
- Process multiple requests together
- Lower per-request cost

### Quantization
- Run smaller precision models (8-bit, 4-bit)
- Faster, uses less memory
- Slight quality trade-off

### Local Deployment
- Llama.cpp, Ollama for local inference
- No API costs
- Requires GPU/CPU resources

## Popular LLM APIs

### OpenAI
```python
from openai import OpenAI
client = OpenAI(api_key="...")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Anthropic (Claude)
```python
from anthropic import Anthropic
client = Anthropic(api_key="...")
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Groq (Ultra-Fast Inference)
```python
from groq import Groq
client = Groq(api_key="...")
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Cost Comparison (per 1M tokens)

| Model | Input | Output |
|-------|-------|--------|
| GPT-4 | $10 | $30 |
| GPT-3.5 Turbo | $0.50 | $1.50 |
| Claude 3.5 Sonnet | $3 | $15 |
| Claude 3 Haiku | $0.25 | $1.25 |
| Groq (Llama 3.3) | $0.59 | $0.79 |

## Best Practices

1. **Start with Clear Instructions**: Be specific about what you want
2. **Use System Prompts**: Set context and behavior
3. **Provide Examples**: Few-shot for consistent formatting
4. **Handle Errors Gracefully**: LLM outputs can be unpredictable
5. **Validate Outputs**: Don't trust blindly
6. **Monitor Costs**: Track token usage
7. **Use Appropriate Models**: Don't use GPT-4 for simple tasks
8. **Implement Retries**: Handle rate limits and failures
9. **Add Guardrails**: Validate inputs and outputs
10. **Log Interactions**: Debug and improve over time

## Evaluation

### Automated Metrics
- BLEU, ROUGE (summarization)
- Accuracy (classification)
- Pass@K (code generation)

### Human Evaluation
- Fluency
- Coherence
- Factuality
- Helpfulness

### LLM-as-Judge
- Use strong LLM to evaluate weaker model outputs
- Cost-effective alternative to human eval

## Future Directions

- **Longer Contexts**: 1M+ tokens becoming standard
- **Multimodality**: Text, images, audio, video
- **Agent Capabilities**: Built-in tool use
- **Personalization**: Adapt to user preferences
- **Efficiency**: Same capability, lower cost
- **Reasoning**: Better at complex logic and math

## Conclusion

LLMs have revolutionized AI applications. Understanding their capabilities, limitations, and best practices is essential for building effective AI systems. As models continue to improve, they'll become even more capable, efficient, and integrated into everyday tools.

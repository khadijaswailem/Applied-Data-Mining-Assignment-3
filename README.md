# CSAI 422: Assignment 3 - Conversational Agents with Tool Use and Reasoning

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install openai python-dotenv requests
```

### 4. Configure Environment Variables
Create a `.env` file in the project root with the following:
```env
# OpenAI API Configuration
API_KEY=your_api_key_here
BASE_URL=https://api.openai.com/v1  # Or your custom endpoint
LLM_MODEL=gpt-4o-mini

# WeatherAPI Configuration (get free key at https://www.weatherapi.com/)
WEATHER_API_KEY=your_weather_api_key_here
```

### 5. Run the Application
```bash
python conversational_agent.py
```

## Implementation Documentation

### Part 1: Basic Tool Calling
- **Weather Tools**: `get_current_weather()` and `get_weather_forecast()` using WeatherAPI
- **Tool Definitions**: JSON schema format for OpenAI API function calling
- **Process Messages**: Handles tool invocation and response processing
- **Conversation Runner**: Interactive CLI for weather queries

### Part 2: Chain of Thought Reasoning
- **Calculator Tool**: Mathematical expression evaluator
- **CoT System Message**: Prompts the model to think step-by-step
- **Enhanced Tools**: Combines weather tools with calculator

### Part 3: Advanced Tool Orchestration
- **Safe Tool Execution**: Validates tool names, parses arguments, handles errors
- **Parallel Execution**: Uses ThreadPoolExecutor for independent tool calls
- **Multi-Step Workflow**: Supports multiple rounds of tool use
- **Structured Outputs**: Validates JSON responses with required keys

## Example Conversations

### Basic Agent
```
Weather Assistant: Hello! I can help you with weather information.
Ask me about the weather anywhere!
(Type 'exit' to end the conversation)

You: What's the weather in Cairo?
Weather Assistant: The current weather in Cairo is sunny with a temperature of 32°C.
```

### Chain of Thought Agent
```
Weather Assistant: Hello! I can help you with weather information.
(Type 'exit' to end the conversation)

You: Which is warmer, Cairo or London?
Weather Assistant: Let me break this down step-by-step:
1. First, I need to get the current weather in both cities.
2. Then I'll compare the temperatures.
[Tool calls executed]
Based on the data, Cairo (32°C) is warmer than London (15°C).
```

### Advanced Agent
```
Advanced Weather Assistant: Hello! Ask me complex weather questions.
(Type 'exit' to end the conversation)

You: What is the temperature difference between Cairo and London?
[Multiple tool iterations executed]
The temperature difference is 17°C, with Cairo being warmer.
```

## Performance Analysis

### Parallel vs Sequential Execution
When querying multiple independent locations, parallel tool execution significantly reduces latency:

| Query Type | Sequential Time | Parallel Time | Speedup |
|------------|-----------------|---------------|---------|
| 3 cities   | ~1.5s          | ~0.5s         | ~3x     |
| 5 cities   | ~2.5s          | ~0.6s         | ~4x     |

**Why Parallel Execution Matters:**
- Independent weather queries have no data dependencies
- Each API call takes ~500ms; sequential = N × 500ms
- Parallel execution: max(500ms) for N queries
- Speedup increases with more independent calls

### Reasoning Strategy Comparison

| Strategy   | Pros                           | Cons                           |
|------------|--------------------------------|--------------------------------|
| Basic      | Fast, simple                  | No step-by-step reasoning     |
| Chain of Thought | Clear reasoning, accurate calculations | Slower, more tokens |
| Advanced   | Multi-step, parallel, structured | Most complex implementation |

### When to Use Each:
- **Basic**: Simple, single-location queries
- **CoT**: Comparison and calculation tasks
- **Advanced**: Multi-location queries and complex workflows

## Challenges and Solutions

1. **API Key Management**: Used `.env` files for secure credential storage
2. **JSON Parsing Errors**: Added try-except blocks in `execute_tool_safely`
3. **Parallel Execution**: Used ThreadPoolExecutor for concurrent API calls
4. **Structured Output Validation**: Implemented `validate_structured_output` function
5. **Maximum Iterations**: Added loop limits to prevent infinite tool calling

## Bonus: Comparative Evaluation

The bonus section implements:
1. Single query processing across all three agent types
2. Sequential vs parallel timing comparison
3. User ratings (1-5) for response quality
4. CSV export for later analysis

Run with option 4 to test the evaluation system.

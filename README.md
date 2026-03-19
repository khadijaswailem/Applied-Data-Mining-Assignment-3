# Conversational Agent — README

## Table of Contents

1. [Setup Instructions](#setup-instructions)
2. [Implementation Overview](#implementation-overview)
3. [Example Conversations](#example-conversations)
4. [Analysis of Reasoning & Orchestration Strategies](#analysis)
5. [Challenges & Solutions](#challenges)

---

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- A [Groq](https://console.groq.com/) API key
- A [WeatherAPI](https://www.weatherapi.com/) key

### Installation

```bash
# 1. Clone or download the project
git clone <your-repo-url>
cd <project-folder>

# 2. Install dependencies
pip install groq python-dotenv requests

# 3. Create your .env file
touch .env
```

### Environment Variables

Add the following to your `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
BASE_URL=https://api.groq.com/openai/v1
OPTOGPT_MODEL=llama3-70b-8192
WEATHER_API_KEY=your_weatherapi_key_here
```

### Running the Agent

```bash
python conversational_agent.py
```

You will be presented with the following menu:

```
Choose a mode:
  1: Basic Agent
  2: Chain of Thought Agent
  3: Advanced Agent
  4: Bonus Evaluation
  5: Parallel vs Sequential Tests
  6: Multi-Step Workflow Tests
Enter choice:
```

> **Note:** Option 4 (Bonus Evaluation) is non-functional. All other options work as expected.

---

## Overview

We have three agent architectures, each built on top of a shared tool layer.

### Part 1: Basic Weather Agent

**Tasks 1.1–1.5**

Two real-time weather functions are implemented: `get_current_weather` and `get_weather_forecast`, both using the WeatherAPI REST endpoint. These functions are LLM tools using the compatible tool schema required by Groq. The `process_messages` function handles the full tool-call loop: sending the user message to the LLM, detecting any tool call requests in the response, executing the appropriate function, and appending the result back into the message history. `run_conversation` puts this into an interactive REPL loop (read,evaluate,print,loop).

### Part 2: Chain of Thought (CoT) Agent

**Tasks 2.1–2.4**

A `calculator` tool is added, which evaluates math expressions using `eval()`. The CoT system prompt tells  the LLM to reason step-by-step: identify what data it needs, break the problem down, call the appropriate tools, explain its reasoning, and deliver a final answer. This agent uses the combined `cot_tools` list (weather + calculator) and the same `process_messages` loop as the basic agent.

### Part 3: Advanced Multi-Step Agent

**Tasks 3.1–3.4**

**Safe tool execution** :`execute_tool_safely` puts every tool call in validation and exception handling, returning a structured JSON object with a `success` flag, so the LLM can handle failures easily rather than crashing.

**Parallel execution**:`execute_tools_parallel` uses `concurrent.futures.ThreadPoolExecutor` to run independent tool calls simultaneously. When the LLM decides to fetch weather for three cities at once, all three HTTP requests work in parallel not one after another. A comparison function, `compare_parallel_vs_sequential`, measures the time of both methods and reports speedup.

**Multi-step loop** : `run_conversation_advanced` loops up to `max_iterations` times per turn, calling `process_messages_advanced`  each time. The loop continues as long as the model keeps returning tool calls, stopping only when it produces a plain-text final answer (or the iteration limit is hit which happened in my testing).

**Structured output** : `get_structured_final_response` appends a system prompt requesting a strict JSON format and validates the response against required keys (`query_type`, `locations`, `summary`, `tool_calls_used`, `final_answer`) before returning it.

---

## Test Conversations Results

### Option 1: Basic Agent

```
Weather Assistant: Hello! I can help you with weather information.
Ask me about the weather anywhere!
(Type 'exit' to end the conversation)

You: cairo

[Tool get_current_weather executed]: {"location": "Cairo",
"temperature_c": 23.3, "temperature_f": 73.9, "condition":
"Partly cloudy", "humidity": 38, "wind_kph": 34.9}

You: exit

Weather Assistant: Goodbye! Have a great day!
```



---

### Option 2: Chain of Thought Agent

```
Weather Assistant: Hello! I can help you with weather information.
Ask me about the weather anywhere!
(Type 'exit' to end the conversation)

You: Is it warmer in Cairo or London, and by how much in Fahrenheit?

Weather Assistant: To find out if Cairo is warmer than London and by how much, we need to compare the temperature of both cities in Fahrenheit. The temperature in Cairo is 72.1°F and in London is 62.6°F.

So, Cairo is warmer than London by 72.1 - 62.6 = 9.5°F

You: exit

Weather Assistant: Goodbye! Have a great day!
```


---

### Option 3: Advanced Agent

```
Advanced Weather Assistant: Hello! Ask me complex weather questions.
I can compare cities, perform calculations, and return structured outputs.
(Type 'exit' to end the conversation)

You: jeddah and cairo

Advanced Weather Assistant: The current weather in Jeddah, Saudi Arabia
is overcast with a temperature of 34.2°C (93.6°F) and 32% humidity. In
Cairo, Egypt, the current weather is partly cloudy with a temperature of
23.3°C (73.9°F) and 38% humidity.

You: exit

Advanced Weather Assistant: Goodbye! Have a great day!

Advanced Weather Assistant: Hello! Ask me complex weather questions.
I can compare cities, perform calculations, and return structured outputs.
(Type 'exit' to end the conversation)

You: Is it warmer in Cairo or London, and by how much in Fahrenheit?

Advanced Weather Assistant: Cairo is warmer than London by 9 Fahrenheit.

You: exit

Advanced Weather Assistant: Goodbye! Have a great day!
```

---

### Option 5: Parallel vs Sequential Tests

**Query: Compare the current weather in Cairo, Riyadh, and London.**

```
Tool calls requested:
  get_current_weather({"location":"Cairo, Egypt"})
  get_current_weather({"location":"Riyadh, Saudi Arabia"})
  get_current_weather({"location":"London, UK"})

Sequential time : 0.6477s
Parallel time   : 0.1810s
Speedup         : 3.58x

Final Answer:
The current weather in Cairo, Riyadh, and London is:

Cairo, Egypt: Partly cloudy, 22.3°C (72.1°F), humidity 33%, wind 35.6 km/h.

Riyadh, Saudi Arabia: Partly cloudy, 23.3°C (73.9°F), humidity 38%, wind 31.7 km/h.

London, UK: Sunny, 17.0°C (62.6°F), humidity 32%, wind 14.4 km/h.
```

**Query: Which city is warmer right now: Paris, Rome, or Berlin?**

```
Sequential time : 1.0600s
Parallel time   : 0.3500s
Speedup         : 3.03x

Final Answer:
Based on the function calls, we can see that the current temperature in Paris is 17.0°C, in Rome is 18.3°C, and in Berlin is 16.1°C. Therefore, Rome is the warmest city.
```

**Query: Give me a short comparison of the weather in Alexandria, Aswan, and Dubai.**

```
Sequential time : 0.5285s
Parallel time   : 0.1670s
Speedup         : 3.16x

Final Answer:
The current weather in Alexandria is partly cloudy with a temperature of 19.2°C (66.6°F), while Aswan is sunny with a temperature of 25.1°C (77.1°F). Dubai is also sunny with a temperature of 39.7°C (103.5°F). The humidity levels are 68% in Alexandria, 22% in Aswan, and 19% in Dubai.
```

---

### Option 6: Multi-Step Workflow Tests

**Query: What is the average maximum temperature in Cairo over the next 3 days?**

```
[Iteration 1] Tool calls made:
  get_weather_forecast({"days":3,"location":"Cairo"}) × 3
  calculator({"expression":"((0 + 25) + (0 + 28) + (0 + 29)) / 3"})

[Iteration 2] Final Answer:
The average maximum temperature in Cairo over the next 3 days is approximately 27.33°C.
```

**Query: Will tomorrow's maximum temperature in Riyadh be higher than today's temperature in Jeddah?**

```
[Iteration 1] get_weather_forecast({"days":1, "location":"Riyadh, Saudi Arabia", "units":"metric"})
[Iteration 2] get_weather_forecast({"days":1, "location":"Riyadh, Saudi Arabia"})
[Iteration 3] get_current_weather({"location":"Jeddah, Saudi Arabia"})

[Iteration 4] Final Answer:
Tomorrow's maximum in Riyadh: 24.9°C
Today's temperature in Jeddah: 34.2°C
→ No — Jeddah is warmer today than Riyadh will be tomorrow.
```

**Query: What is the temperature difference between Cairo and London right now?**

```
[Iteration 1] Tool calls made:
  get_current_weather({"location":"Cairo, Egypt"})
  get_current_weather({"location":"London, England"})
  calculator({"expression":"get(\"temp\")[1] - get(\"temp\")[0]"})

[Iteration 2] Tool calls made:
  calculator({"expression":"get(\"weather_locations\")[1](\"temperature_c\") - get(\"weather_locations\")[0](\"temperature_c\")"})

[Iteration 3] Tool calls made:
  get_current_weather({"location":"Cairo, Egypt"})
  get_current_weather({"location":"London, England"})
  calculator({"expression":"[\"temperature_c\"][-1] - [\"temperature_c\"][0]"})

[Iteration 4] Tool calls made:
  calculator({"expression":"float([\"temperature_c\"][-1]) - float([\"temperature_c\"][0])"})

[Iteration 5] Tool calls made:
  calculator({"expression":"(weather_locations[1])['temperature_c'] - (weather_locations[0])['temperature_c']"})
  get_current_weather({"location":"Cairo, Egypt"})
  get_current_weather({"location":"London, England"})
  calculator({"expression":"(weather_locations[1])['temperature_c'] - (weather_locations[0])['temperature_c']"})

[Stopped] Reached max iterations (5).
```

---

## Analysis of Reasoning & Orchestration Strategies

### Basic Agent

The basic agent is good for single-city queries. It maps natural-language input (even a just a city name) to a tool call and returns structured JSON data. Its main limitation is that it doesnt have a reasoning layer and it cannot perform calculations or compare multiple results. The output is also raw JSON.

### Chain of Thought Agent

The CoT system prompt improves the agent's behavior on complex queries by instructing it to plan before acting. With "Is it warmer in Cairo or London, and by how much in Fahrenheit?", the agent needed to sequence tool calls and then compute a result and it also formatted it in natural-language and reasoned about its steps to getting the response it generated. 

### Advanced Agent

The advanced agent fetched 2 cities in parallel and returned a natural-language summary and no raw JSON was printed which is an improvement over the basic agent's output.It was also able to compare between 2, cairo and london and calculate the temperature difference between them in Farenheit, and the result was in a summarized one line sentence "Cairo is warmer than London by 9 Fahrenheit", without the reasoning steps in the COT agent.

### Parallel execution

Produced consistent and measurable speedups. Across all three test queries, parallel execution was 2.1x to 3.2x (varies from ne run to the other) faster than sequential. The speedup grows with the number of independent tool calls, which aligns with the expectation that for N independent network requests, the ideal speedup is N×. The observed ratios are slightly below the theoretical ceiling because of thread-pool overhead but they are still good.

### Multi-step reasoning

Allowed the agent to iteratively improve its approach. In the Riyadh vs. Jeddah query, the model initially passed an unsupported `units` parameter to the API (iteration 1), then retried without it (iteration 2), then gathered the Jeddah data (iteration 3), and created a final answer on iteration 4. This seamless retry behavior was possible because the multi-step loop kept the conversation on across failed tool calls.



## Challenges & Solutions

### Challenge 1: Infinite iterations loop causing a crash

**What happened:** In Option 6, the query "What is the temperature difference between Cairo and London?" caused the agent to loop through all 5 iterations without reaching a final answer. 


**Solution applied:** The multi-step loop's `max_iterations=5` prevented an infinite loop and let the program continue. 

---


### Challenge 2: Bonus Evaluation (Option 4) Not Working

**What happened:** Option 4 did not execute successfully during testing.


**Mitigation:** The function was left in the code as a trial implementation. A more better version would separate the automated evaluation phase (running all three agents) from the interactive rating phase, and handle non-integer or empty input easily.

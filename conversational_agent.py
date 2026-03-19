import os
import json
from pyexpat.errors import messages
from groq import Groq 
from dotenv import load_dotenv
import requests
from concurrent.futures import ThreadPoolExecutor
import time

load_dotenv()
API_KEY = os.environ.get("API_KEY", os.getenv("GROQ_API_KEY"))
BASE_URL = os.environ.get("BASE_URL", os.getenv("BASE_URL"))
LLM_MODEL = os.environ.get("LLM_MODEL", os.getenv("OPTOGPT_MODEL"))

client = Groq(
     api_key=API_KEY,
     base_url=BASE_URL,
)

#PART 1
#TASK 1.1
def get_current_weather(location):
    """current weather for a location"""
    api_key = os.environ.get("WEATHER_API_KEY")#retrieving API key from env
    url = (
        f"http://api.weatherapi.com/v1/current.json"#base endpoint for current weather
        f"?key={api_key}&q={location}&aqi=no"#API key, location query, and no air quality data
    )
    response = requests.get(url)#GET request to the weather API
    data = response.json()#API response to dictionary
    if "error" in data:#if API returned an error
        return f"Error: {data['error']['message']}"
    weather_info = data["current"]#extracting current weather info from API response
    return json.dumps(#returning weather info as JSON string
        {
            "location": data["location"]["name"],
            "temperature_c": weather_info["temp_c"],
            "temperature_f": weather_info["temp_f"],
            "condition": weather_info["condition"]["text"],
            "humidity": weather_info["humidity"],
            "wind_kph": weather_info["wind_kph"],
        }
    )


def get_weather_forecast(location, days=3):
    """weather forecast for a location for a specified number of days"""
    api_key = os.environ.get("WEATHER_API_KEY")
    url = (
        f"http://api.weatherapi.com/v1/forecast.json"
        f"?key={api_key}&q={location}&days={days}&aqi=no"
    )
    response = requests.get(url)
    data = response.json()
    if "error" in data:
        return f"Error: {data['error']['message']}"
    forecast_days = data["forecast"]["forecastday"]#extracting list of forecast days
    forecast_data = []#list to store forecast info
    for day in forecast_days:#looping through each day's forecast
        forecast_data.append(#adding data for each day
            {
                "date": day["date"],
                "max_temp_c": day["day"]["maxtemp_c"],
                "min_temp_c": day["day"]["mintemp_c"],
                "condition": day["day"]["condition"]["text"],
                "chance_of_rain": day["day"]["daily_chance_of_rain"],
            }
        )
    return json.dumps(#converting result to JSON string
        {
            "location": data["location"]["name"],
            "forecast": forecast_data,
        }
    )


#TASK 1.2
weather_tools = [#list of tool configurations
    {
        "type": "function",#specifying tool type as function
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",#defining parameters as json object
                "properties": {
                    "location": {
                        "type": "string",
                        "description": (
                            "The city and state, e.g., San Francisco, CA, "
                            "or a country, e.g., France"#explaining expected input format
                        ),
                    }
                },
                "required": ["location"],#making location a required parameter
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": (
                "Get the weather forecast for a location for a specific "
                "number of days"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": (
                            "The city and state, e.g., San Francisco, CA, "
                            "or a country, e.g., France"
                        ),
                    },
                    "days": {
                        "type": "integer",
                        "description": "The number of days to forecast (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["location"],
            },
        },
    },
]

available_functions = {#mapping function names to functions
    "get_current_weather": get_current_weather,
    "get_weather_forecast": get_weather_forecast,
}


#TASK 1.3
def process_messages(client, messages, tools=None, available_functions=None):
    """process messages and invoke tools as needed"""
    tools = tools or []#using empty list if tools is None
    available_functions = available_functions or {}#same here

    response = client.chat.completions.create(#sending messages to llm client for response
        model=LLM_MODEL,
        messages=messages,
        tools=tools,
    )
    response_message = response.choices[0].message#getting the first message from llm response

    messages.append(response_message)#adding llm response to messages

    if response_message.tool_calls:#checking if llm wants to call a tool
        for tool_call in response_message.tool_calls:#looping through each tool call
            function_name = tool_call.function.name#extracting tool function name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)#parsing arguments from json string
            function_response = function_to_call(**function_args)

            messages.append(#adding tool response to messages
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )

    return messages


#TASK 1.4
def run_conversation(client, system_message="You are a helpful weather assistant."):
    messages = [{"role": "system", "content": system_message}]#initializing messages with system prompt
    print("Weather Assistant: Hello! I can help you with weather information.")
    print("Ask me about the weather anywhere!")
    print("(Type 'exit' to end the conversation)\n")

    while True:#conversation loop
        user_input = input("You: ")#getting input from user
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\nWeather Assistant: Goodbye! Have a great day!")
            break

        messages.append({"role": "user", "content": user_input})#adding user message to conversation

        #send message to llm
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=weather_tools,
        )

        #getting the assistant message
        assistant_msg = response.choices[0].message
        messages.append(assistant_msg)#adding it to the response

        #printing assistant content 
        if getattr(assistant_msg, "content", None):
            print(f"\nWeather Assistant: {assistant_msg.content}\n")

        #executing tool calls
        if getattr(assistant_msg, "tool_calls", None):#checking if assistant calls any tools
            for tool_call in assistant_msg.tool_calls:#loop through each tool call
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                func = available_functions[func_name]
                tool_output = func(**func_args)

                print(f"\n[Tool {func_name} executed]: {tool_output}\n")

                #appending tool output as message for llm
                messages.append(
                    {
                        "role": "tool",
                        "name": func_name,
                        "content": tool_output,
                        "tool_call_id": tool_call.id,
                    }
                )


#TASK 1.5
# if __name__ == "__main__":
#     run_conversation(client)


#PART 2
#TASK 2.1
def calculator(expression):
    """evaluates a mathematical expression"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


#TASK 2.2
calculator_tool = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate a mathematical expression",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "The mathematical expression to evaluate, "
                        "e.g., '2 + 2' or '5 * (3 + 2)'"
                    ),
                }
            },
            "required": ["expression"],
        },
    },
}

cot_tools = weather_tools + [calculator_tool]#combining weather tools and calculator tool into one list
available_functions["calculator"] = calculator #adding calculator function to available functions


#TASK 2.3   
cot_system_message = """You are a helpful assistant that can answer questions
about weather and perform calculations.
When responding to complex questions, please follow these steps:
1. Think step-by-step about what information you need.
2. Break down the problem into smaller parts.
3. Use the appropriate tools to gather information.
4. Explain your reasoning clearly.
5. Provide a clear final answer.
For example, if someone asks about temperature conversions or
comparisons between cities, first get the weather data, then use the
calculator if needed, showing your work.
"""

#TASK 2.4
# if __name__ == "__main__":
#     print("Testing Chain of Thought Agent:")
#     run_conversation(client, cot_system_message)


#PART 3
#TASK 3.1
def execute_tool_safely(tool_call, available_functions):
    """tool call with validation and error handling"""
    function_name = tool_call.function.name#extracting function name from tool call

    if function_name not in available_functions:#checking if function exists in available functions
        return json.dumps(
            {
                "success": False,
                "error": f"Unknown function: {function_name}",
            }
        )

    try:
        function_args = json.loads(tool_call.function.arguments)#parsing arguments from json string
    except json.JSONDecodeError as e:
        return json.dumps(
            {
                "success": False,
                "error": f"Invalid JSON arguments: {str(e)}",
            }
        )

    try:
        function_response = available_functions[function_name](**function_args)#calling function with arguments
        return json.dumps(
            {
                "success": True,
                "function_name": function_name,
                "result": function_response,
            }
        )
    except TypeError as e:
        return json.dumps(
            {
                "success": False,
                "error": f"Invalid arguments: {str(e)}",
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
            }
        )


#TASK 3.2
def execute_tools_sequential(tool_calls, available_functions):
    """executes tool calls one after another"""
    results = []
    for tool_call in tool_calls:
        safe_result = execute_tool_safely(tool_call, available_functions)#executing tool call with error handling
        tool_message = {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_call.function.name,
            "content": safe_result,
        }
        results.append(tool_message)#appending result to list of results
    return results


def execute_tools_parallel(tool_calls, available_functions, max_workers=4):
    """executes independent tool calls in parallel"""

    def run_single_tool(tool_call):
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_call.function.name,
            "content": execute_tool_safely(tool_call, available_functions),
        }

    with ThreadPoolExecutor(#using thread pool to execute tool calls in parallel
        max_workers=min(max_workers, len(tool_calls))
    ) as executor:
        return list(executor.map(run_single_tool, tool_calls))


def compare_parallel_vs_sequential(tool_calls, available_functions):
    """measures the timing difference between sequential and parallel"""
    start = time.perf_counter()
    sequential_results = execute_tools_sequential(tool_calls, available_functions)
    sequential_time = time.perf_counter() - start

    start = time.perf_counter()
    parallel_results = execute_tools_parallel(tool_calls, available_functions)
    parallel_time = time.perf_counter() - start

    speedup = (
        sequential_time / parallel_time if parallel_time > 0 else None
    )

    return {
        "sequential_results": sequential_results,
        "parallel_results": parallel_results,
        "sequential_time": sequential_time,
        "parallel_time": parallel_time,
        "speedup": speedup,
    }


#TASK 3.3
advanced_tools = cot_tools
advanced_system_message = """You are a helpful weather assistant that can use
weather tools and a calculator to solve multi-step problems.
Guidelines:
1. If the user asks about several independent locations, use multiple weather
tool calls in parallel when appropriate.
2. If a question requires several steps, continue using tools until the task is
completed.
3. If a tool fails, explain the issue clearly and continue safely when possible.
4. For complex comparison or calculation queries, prepare a structured final
response.
"""


def process_messages_advanced(client, messages, tools=None, available_functions=None):
    """sends messages to the model and execute any returned tools in parallel"""
    tools = tools or []
    available_functions = available_functions or {}

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=tools,
    )
    response_message = response.choices[0].message
    messages.append(response_message)

    if response_message.tool_calls:
        tool_results = execute_tools_parallel(
            response_message.tool_calls,
            available_functions,
        )
        messages.extend(tool_results)

    return messages, response_message


def run_conversation_advanced(
    client,
    system_message=advanced_system_message,
    max_iterations=5,
):
    """runs a conversation that supports multi step tool workflows"""
    messages = [
        {
            "role": "system",
            "content": system_message,
        }
    ]
    print("Advanced Weather Assistant: Hello! Ask me complex weather questions.")
    print("I can compare cities, perform calculations, and return structured outputs.")
    print("(Type 'exit' to end the conversation)\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\nAdvanced Weather Assistant: Goodbye! Have a great day!")
            break

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        for _ in range(max_iterations):
            messages, response_message = process_messages_advanced(
                client, messages, advanced_tools, available_functions
            )

            if not response_message.tool_calls:
                #print the final answer once the model stops calling tools
                final_content = getattr(response_message, "content", None)
                if final_content:
                    print(f"\nAdvanced Weather Assistant: {final_content}\n")
                break
        else:
            print(
                "\nAdvanced Weather Assistant: I stopped after reaching the"
                " maximum number of tool iterations.\n"
            )

    return messages  # outside the while loop so the conversation keeps going
    

#TASK 3.4
required_output_keys = [#keys that must be included in the final JSON output for complex queries
    "query_type",
    "locations",
    "summary",
    "tool_calls_used",
    "final_answer",
]

#defining structured output instructions for llm responses
structured_output_prompt = """For complex comparison or calculation queries,
return the final answer as a valid JSON object with exactly these keys:
- query_type
- locations
- summary
- tool_calls_used
- final_answer
Do not include markdown fences.
"""

def validate_structured_output(response_text):
    """validate the final structured JSON response"""
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON output: {str(e)}")

    for key in required_output_keys:
        if key not in parsed:
            raise ValueError(f"Missing required key: {key}")

    if not isinstance(parsed["locations"], list):
        raise ValueError("'locations' must be a list")

    if not isinstance(parsed["tool_calls_used"], list):
        raise ValueError("'tool_calls_used' must be a list")

    return parsed


def get_structured_final_response(client, messages):
    """requests a structured final response in JSON mode and validate it"""
    structured_messages = messages + [
        {
            "role": "system",
            "content": structured_output_prompt,
        }
    ]

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=structured_messages,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    validated = validate_structured_output(content)
    return validated


#Extra functions to run each agent type
def run_basic_agent(client, user_query):
    """runs the basic agent for a single query"""
    messages = [
        {"role": "system", "content": "You are a helpful weather assistant."},
        {"role": "user", "content": user_query},
    ]
    messages = process_messages(client, messages, weather_tools, available_functions)
    return messages[-1].get("content", "No response")


def run_cot_agent(client, user_query):
    """runs the Chain of Thought agent for a single query"""
    messages = [
        {"role": "system", "content": cot_system_message},
        {"role": "user", "content": user_query},
    ]
    messages = process_messages(client, messages, cot_tools, available_functions)
    return messages[-1].get("content", "No response")


def run_advanced_agent(client, user_query, max_iterations=5):
    """runs the advanced agent for a single query"""
    messages = [
        {"role": "system", "content": advanced_system_message},
        {"role": "user", "content": user_query},
    ]
    for _ in range(max_iterations):
        messages, response_message = process_messages_advanced(
            client, messages, advanced_tools, available_functions
        )
        if not response_message.tool_calls:
            break
    #return messages[-1].get("content", "No response")
    return getattr(messages[-1], "content", None) or messages[-1].get("content", "No response")


#BONUS TASK
def bonus_evaluation():
    """comparative evaluation system"""
    import csv

    user_query = input("Enter a query to evaluate across all agents: ")

    print("\n" + "=" * 60)
    print("Running Basic Agent...")
    basic_response = run_basic_agent(client, user_query)
    print(f"Basic Agent Response: {basic_response}\n")

    print("=" * 60)
    print("Running Chain of Thought Agent...")
    cot_response = run_cot_agent(client, user_query)
    print(f"CoT Agent Response: {cot_response}\n")

    print("=" * 60)
    print("Running Advanced Agent...")
    advanced_response = run_advanced_agent(client, user_query)
    print(f"Advanced Agent Response: {advanced_response}\n")

    print("=" * 60)
    print("Testing Parallel vs Sequential Execution...")
    print("Query: Compare weather in Cairo, Riyadh, and London")

    test_messages = [
        {"role": "system", "content": "You are a helpful weather assistant."},
        {"role": "user", "content": "Compare the current weather in Cairo, Riyadh, and London."},
    ]

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=test_messages,
        tools=weather_tools,
    )

    tool_calls = response.choices[0].message.tool_calls or []
    if tool_calls:
        timing_results = compare_parallel_vs_sequential(tool_calls, available_functions)
        print(f"Sequential time: {timing_results['sequential_time']:.4f}s")
        print(f"Parallel time: {timing_results['parallel_time']:.4f}s")
        print(f"Speedup: {timing_results['speedup']:.2f}x")
    else:
        print("No tool calls were made for timing comparison.")

    print("\n" + "=" * 60)
    print("Rating Phase")
    print("Rate each response on a scale of 1-5:\n")

    basic_rating = int(input(f"Basic Agent rating (1-5): "))
    cot_rating = int(input(f"Chain of Thought Agent rating (1-5): "))
    advanced_rating = int(input(f"Advanced Agent rating (1-5): "))

    results = [
        ["Agent", "Rating", "Response"],
        ["Basic", basic_rating, basic_response[:200]],
        ["Chain of Thought", cot_rating, cot_response[:200]],
        ["Advanced", advanced_rating, advanced_response[:200]],
    ]

    with open("evaluation_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(results)

    print("\nResults saved to evaluation_results.csv")


#Parallel vs Sequential Test Runner (TASK 3.2)
def run_parallel_test(client, user_query):
    """
    For a given multi-city query:
      1. Asks the LLM which tools to call (returns one tool_call per city)
      2. Runs those tool calls both sequentially AND in parallel
      3. Prints a timing comparison and the final LLM answer
    """
    print(f"\n{'='*60}")
    print(f"Query: {user_query}")
    print('='*60)

    #Send the query to the LLM to get tool_calls
    messages = [
        {"role": "system", "content": advanced_system_message},
        {"role": "user",   "content": user_query},
    ]
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=advanced_tools,
    )
    assistant_msg = response.choices[0].message
    tool_calls = assistant_msg.tool_calls or []

    if not tool_calls:
        print("No tool calls were made the model answered directly:")
        print(assistant_msg.content)
        return

    print("Tool calls requested:")
    for tc in tool_calls:
        print(f"  {tc.function.name}({tc.function.arguments})")
    print()

    #Comparing sequential vs parallel execution timing
    timing = compare_parallel_vs_sequential(tool_calls, available_functions)
    print(f"Sequential time : {timing['sequential_time']:.4f}s")
    print(f"Parallel time   : {timing['parallel_time']:.4f}s")
    if timing['speedup']:
        print(f"Speedup         : {timing['speedup']:.2f}x")

    #Feed the parallel results back to get the final LLM answer
    messages.append(assistant_msg)
    messages.extend(timing['parallel_results'])

    final_response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=advanced_tools,
    )
    final_answer = final_response.choices[0].message.content
    print(f"\nFinal Answer:\n{final_answer}\n")


def run_all_parallel_tests(client):
    """runs all three test prompts."""
    test_prompts = [
        "Compare the current weather in Cairo, Riyadh, and London.",
        "Which city is warmer right now: Paris, Rome, or Berlin?",
        "Give me a short comparison of the weather in Alexandria, Aswan, and Dubai.",
    ]
    print("\n" + "="*60)
    print("Parallel vs Sequential Execution Tests")
    print("="*60)
    for prompt in test_prompts:
        run_parallel_test(client, prompt)


#Multi-Step Tool Workflow Tests (TASK 3.3)
def run_multistep_test(client, user_query, max_iterations=5):
    """
    runs a single query through the advanced multi-step agent and print
    each tool-call so we can see the workflow in action
    """
    print(f"\n{'='*60}")
    print(f"Query: {user_query}")
    print('='*60)

    messages = [
        {"role": "system", "content": advanced_system_message},
        {"role": "user",   "content": user_query},
    ]

    for iteration in range(1, max_iterations + 1):
        messages, response_message = process_messages_advanced(
            client, messages, advanced_tools, available_functions
        )

        #which tools were called in this round
        if response_message.tool_calls:
            print(f"\n[Iteration {iteration}] Tool calls made:")
            for tc in response_message.tool_calls:
                print(f"  {tc.function.name}({tc.function.arguments})")
        else:
            #No more tool calls, model has reached its final answer
            final_content = getattr(response_message, "content", None)
            print(f"\n[Iteration {iteration}] Final Answer:\n{final_content}\n")
            break
    else:
        print(f"\n[Stopped] Reached max iterations ({max_iterations}).\n")


def run_all_multistep_tests(client):
    """Runs all test prompts."""
    test_prompts = [
        "What is the temperature difference between Cairo and London right now?",
        "What is the average maximum temperature in Cairo over the next 3 days?",
        "Will tomorrow's maximum temperature in Riyadh be higher than today's temperature in Jeddah?",
    ]
    print("\n" + "="*60)
    print("Multi-Step Tool Workflow Tests")
    print("="*60)
    for prompt in test_prompts:
        run_multistep_test(client, prompt)


#TASK 3.5
if __name__ == "__main__":
    choice = input(
        "Choose a mode:\n"
        "  1: Basic Agent\n"
        "  2: Chain of Thought Agent\n"
        "  3: Advanced Agent\n"
        "  4: Bonus Evaluation\n"
        "  5: Parallel vs Sequential Tests\n"
        "  6: Multi-Step Workflow Tests\n"
        "Enter choice: "
    )
    if choice == "1":
        run_conversation(client, "You are a helpful weather assistant.")
    elif choice == "2":
        run_conversation(client, cot_system_message)
    elif choice == "3":
        run_conversation_advanced(client, advanced_system_message)
    elif choice == "4":
        bonus_evaluation()
    elif choice == "5":
        run_all_parallel_tests(client)
    elif choice == "6":
        run_all_multistep_tests(client)
    else:
        print("Invalid choice. Defaulting to Basic agent.")
        run_conversation(client, "You are a helpful weather assistant.")
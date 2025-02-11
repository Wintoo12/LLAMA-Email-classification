from crewai import Agent, Task, Crew, Process
import os
import litellm
import time
import json

# ✅ Define API Key & Base URL
GROQ_API_KEY = "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"
GROQ_API_BASE = "https://api.groq.com/openai/v1"
MODEL_NAME = "groq/llama3-8b-8192"

# ✅ Set API Key Environment Variables
os.environ["OPENAI_API_BASE"] = GROQ_API_BASE
os.environ["OPENAI_API_KEY"] = GROQ_API_KEY
os.environ["LITELLM_LOG"] = "DEBUG"

# ✅ Explicitly set API key for LiteLLM
litellm.api_key = GROQ_API_KEY
litellm.api_base = GROQ_API_BASE

# ✅ Function to Handle Rate Limits Dynamically
def call_litellm_with_retry(messages, retries=5):
    wait_time = 20  # Default wait time for backoff
    for attempt in range(retries):
        try:
            response = litellm.completion(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=150,  # 🔹 Reduce max tokens to reduce API load
                api_base=GROQ_API_BASE,
                api_key=GROQ_API_KEY
            )
            if response and response.choices[0].message.content.strip():
                return response  # ✅ Return valid response
            else:
                print(f"⚠️ Empty response on attempt {attempt+1}, retrying...")
        except litellm.RateLimitError as e:
            try:
                error_details = json.loads(str(e))
                wait_time = float(error_details["error"]["message"].split("Please try again in ")[1].split("s")[0]) + 1  # 🔹 Extract wait time and add buffer
            except (KeyError, IndexError, ValueError):
                wait_time = 20  # 🔹 Default to 20s if parsing fails
            
            print(f"🚨 Rate limit hit! Waiting {wait_time:.2f}s before retrying...")
            time.sleep(wait_time)  # 🔹 Wait dynamically based on API error
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            break
    return None  # ❌ Return None if all retries fail

# ✅ Test API Before Running CrewAI
try:
    response = call_litellm_with_retry([{"role": "user", "content": "Hello, how are you?"}])
    if response:
        print("✅ LiteLLM Model Response:", response)
    else:
        print("⚠️ No response received. Skipping CrewAI execution.")
        exit(1)  

    email = "Free iPhone! Click on this link and input the details with your credit card details."

    # ✅ CrewAI Agents
    organizer = Agent(
        role="Organizer",
        goal="Ensure the email classification process reaches a valid final answer. Stop until 8 responses.",
        backstory="You oversee email classification and ensure a final decision is reached efficiently. Your say is really important for this case, you are the one who'll be the one who'll give the real answer.",
        verbose=True,
        allow_delegation=False,
        llm=MODEL_NAME  # ✅ Pass only the model name, not a dictionary
    )

    classifier = Agent(
        role="Email Classifier",
        goal="Classify emails as 'important', 'spam', or 'casual'.",
        backstory="You analyze emails to determine their category.",
        verbose=True,
        allow_delegation=True,
        llm=MODEL_NAME  # ✅ Pass only the model name
    )

    responder = Agent(
        role="Email Responder",
        goal="Write responses that seems like an insult but a good one do some trash talks too.",
        backstory="You ensure appropriate responses are given.",
        verbose=True,
        allow_delegation=False,
        llm=MODEL_NAME  # ✅ Pass only the model name
    )

    # ✅ Tasks
    classify_email = Task(
        description=f"Classify the email: '{email}'",
        agent=classifier,
        expected_output="One of: 'important', 'spam', or 'casual'."
    )

    respond_to_email = Task(
        description=f"Write a response to the email: '{email}' based on the classification.",
        agent=responder,
        expected_output="A short, polite response based on classification."
    )

    finalize_decision = Task(
        description="Verify the classification and response. If correct, confirm the final classification and response. Stop after 5 exchanges.",
        agent=organizer,
        expected_output="A final statement confirming the classification and response."
    )

    # ✅ CrewAI Execution
    crew = Crew(
        agents=[classifier, responder, organizer],
        tasks=[classify_email, respond_to_email, finalize_decision],
        verbose=True,
        process=Process.sequential
    )

    output = crew.kickoff()
    print("🚀 CrewAI Output:", output)

except Exception as e:
    print(f"❌ An error occurred: {str(e)}")

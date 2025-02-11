from crewai import Agent, Task, Crew, Process
import os
import litellm
import time

# ✅ Set API Key & Base URL
GROQ_API_KEY = "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"
GROQ_API_BASE = "https://api.groq.com/openai/v1"
MODEL_NAME = "groq/llama3-8b-8192"  # ✅ Use full provider model name

# ✅ Set API Key Environment Variables
os.environ["OPENAI_API_BASE"] = GROQ_API_BASE
os.environ["OPENAI_API_KEY"] = GROQ_API_KEY
os.environ["LITELLM_LOG"] = "DEBUG"

# ✅ Function to Handle Rate Limits with Exponential Backoff
def call_litellm_with_retry(messages, retries=5, wait_time=5):
    for attempt in range(retries):
        try:
            response = litellm.completion(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=250,
                api_base=GROQ_API_BASE,
                api_key=GROQ_API_KEY
            )
            if response and response.choices[0].message.content.strip():
                return response
            else:
                print(f"⚠️ Received empty response on attempt {attempt+1}, retrying...")
        except litellm.RateLimitError:
            print(f"🚨 Rate limit hit! Waiting {wait_time}s before retrying...")
            time.sleep(wait_time)
            wait_time *= 2
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            break
    return None

# ✅ Test LiteLLM Before Running CrewAI
try:
    response = call_litellm_with_retry([{"role": "user", "content": "Hello, how are you?"}])

    if response:
        print("✅ LiteLLM Model Response:", response)
    else:
        print("⚠️ No response received. Skipping CrewAI execution.")
        exit(1)

    email = "nigerian prince sending some gold"

    # ✅ EXPLICITLY Pass API Base & Key in CrewAI Agents
    llm_config = {
        "model": MODEL_NAME,
        "api_base": GROQ_API_BASE,
        "api_key": GROQ_API_KEY
    }

    classifier = Agent(
        role="email classifier",
        goal="Accurately classify emails as 'important', 'spam', or 'casual'.",
        backstory="You are an AI assistant focused on email classification.",
        verbose=True,
        allow_delegation=True,
        llm=llm_config  # ✅ Pass full API config
    )

    responder = Agent(
        role="email responder",
        goal="Write concise and polite responses based on the email's importance.",
        backstory="Your job is to reply to emails based on the classification result.",
        verbose=True,
        allow_delegation=False,
        llm=llm_config  # ✅ Pass full API config
    )

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

    crew = Crew(
        agents=[classifier, responder],
        tasks=[classify_email, respond_to_email],
        verbose=True,
        process=Process.sequential
    )

    # ✅ Run CrewAI
    output = crew.kickoff()
    print("🚀 CrewAI Output:", output)

except Exception as e:
    print(f"❌ An error occurred: {str(e)}")

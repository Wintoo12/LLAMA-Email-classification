from crewai import Agent, Task, Crew, Process
import os
import litellm

# ✅ Define API Key & Base URL
GROQ_API_KEY = "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"
GROQ_API_BASE = "https://api.groq.com/openai/v1"
MODEL_NAME = "groq/llama3-8b-8192"

# ✅ Set API Key Environment Variables (For Debugging)
os.environ["OPENAI_API_BASE"] = GROQ_API_BASE
os.environ["OPENAI_API_KEY"] = GROQ_API_KEY
os.environ["LITELLM_LOG"] = "DEBUG"

# ✅ Force LiteLLM to Recognize API Key Before Running CrewAI
litellm.api_key = GROQ_API_KEY
litellm.api_base = GROQ_API_BASE

# ✅ Test LiteLLM Before Running CrewAI
try:
    response = litellm.completion(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        max_tokens=500,
        api_base=GROQ_API_BASE,  # ✅ Explicitly pass API base
        api_key=GROQ_API_KEY     # ✅ Explicitly pass API key
    )

    print("✅ LiteLLM Model Response:", response)

    email = "Please claim your free iPhone. You may reply with your credit card details."

    # ✅ Explicitly Pass API Key & Base in CrewAI llm
    llm_config = {
        "model": MODEL_NAME,
        "api_base": GROQ_API_BASE,
        "api_key": GROQ_API_KEY
    }

    supervisor = Agent(
        role="organizer",
        goal="Ensure that the email classification process reaches a valid final answer. Give the answer final verdict in 5 responses",
        backstory="You are an AI overseeing the email classification process. Your job is to verify if the email has been correctly classified and provide the final answer and you'll be the one who'll stop the talk between the classifier and responder.",
        verbose=True,
        allow_delegation=False,
        llm=MODEL_NAME  # ✅ Use the same model
    )

    classifier = Agent(
        role="email classifier",
        goal="Accurately classify emails as 'important', 'spam', or 'casual'.",
        backstory="You are an AI assistant focused on email classification.",
        verbose=True,
        allow_delegation=True,
        llm=MODEL_NAME  # ✅ Use model as a string
    )

    responder = Agent(
        role="email responder",
        goal="Write concise and polite responses based on the email's importance.",
        backstory="Your job is to reply to emails based on the classification result.",
        verbose=True,
        allow_delegation=False,
        llm=MODEL_NAME  # ✅ Use model as a string
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

    finalize_decision = Task(
        description=f"Verify if the email classification and response are correct. If they are, confirm the final classification and response.",
        agent=supervisor,
        expected_output="A final statement confirming the classification and response."
    )


    crew = Crew(
        agents=[classifier, responder],
        tasks=[classify_email, respond_to_email, finalize_decision],
        verbose=True,
        process=Process.sequential
    )

    # ✅ Run CrewAI
    output = crew.kickoff()
    print("🚀 CrewAI Output:", output)

except Exception as e:
    print(f"❌ An error occurred: {str(e)}")

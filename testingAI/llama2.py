from crewai import Agent, Task, Crew, Process
import os
import litellm

# API Configuration
GROQ_API_KEY = "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"
GROQ_API_BASE = "https://api.groq.com/openai/v1"
MODEL_NAME = "groq/llama3-8b-8192"

# Configure environment
os.environ["OPENAI_API_BASE"] = GROQ_API_BASE
os.environ["OPENAI_API_KEY"] = GROQ_API_KEY
litellm.api_key = GROQ_API_KEY
litellm.api_base = GROQ_API_BASE

def main():
    try:
        # The email to analyze
        email = "Nigerian prince sending some gold"

        # Create agents with more specific goals
        classifier = Agent(
            role='Email Classifier',
            goal='Analyze emails in detail and provide comprehensive classification with explanation',
            backstory='You are an expert email analyst who provides detailed classifications and explanations for why an email falls into a particular category. You always explain your reasoning.',
            llm=MODEL_NAME,
            verbose=True
        )

        responder = Agent(
            role='Email Responder',
            goal='Create detailed and appropriate responses based on email classification',
            backstory='You are an expert at crafting detailed, appropriate responses that address the specific nature of each email. You provide context and explanation for your responses.',
            llm=MODEL_NAME,
            verbose=True
        )

        organizer = Agent(
            role='Organizer',
            goal='Ensure thorough analysis and appropriate responses',
            backstory='You review classifications and responses to ensure they are complete and appropriate. You provide detailed feedback and suggestions.',
            llm=MODEL_NAME,
            verbose=True
        )

        # Create tasks with detailed expectations
        task1 = Task(
            description=f"""
            Analyze this email in detail: '{email}'
            1. Determine if it's spam, important, or casual
            2. Explain why you classified it this way
            3. List any suspicious or notable elements
            4. Provide a risk assessment if applicable
            """,
            agent=classifier,
            expected_output="A detailed classification report including category, reasoning, and risk assessment"
        )

        task2 = Task(
            description=f"""
            Based on the classification of this email: '{email}'
            1. Create an appropriate response
            2. Explain why this response is appropriate
            3. Include any necessary warnings or advice
            4. Suggest any follow-up actions if needed
            """,
            agent=responder,
            expected_output="A complete response strategy including the response text and explanation of approach"
        )

        task3 = Task(
            description="""
            Review the classification and response:
            1. Verify the classification is appropriate
            2. Confirm the response addresses all concerns
            3. Add any additional recommendations
            4. Provide a final summary of actions taken
            """,
            agent=organizer,
            expected_output="A comprehensive review and final recommendations"
        )

        # Create crew with correct verbose setting
        crew = Crew(
            agents=[classifier, responder, organizer],
            tasks=[task1, task2, task3],
            process=Process.sequential,
            verbose=True  # Changed from 2 to True
        )

        # Execute and print results
        print("\n🔍 Analyzing email:", email)
        result = crew.kickoff()
        print("\n📋 Analysis Results:")
        print(result)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
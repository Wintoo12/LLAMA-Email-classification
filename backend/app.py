from flask import Flask, request, jsonify
from crewai import Agent, Task, Crew, Process
import os
import litellm
from flask_cors import CORS
import traceback
from gmail_service import GmailService  # New import

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

# API Configuration
GROQ_API_KEY = "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"
GROQ_API_BASE = "https://api.groq.com/openai/v1"
MODEL_NAME = "groq/llama3-8b-8192"

# Configure environment variables for LiteLLM
os.environ["OPENAI_API_BASE"] = GROQ_API_BASE
os.environ["OPENAI_API_KEY"] = GROQ_API_KEY
litellm.api_key = GROQ_API_KEY
litellm.api_base = GROQ_API_BASE

# Initialize Gmail Service
gmail_service = GmailService()

def create_agents_and_tasks(email):
    try:
        print(f"Creating agents for email: {email}")  # Debugging

        # Create agents
        classifier = Agent(
            role='Email Classifier',
            goal="Analyze emails in detail and provide comprehensive classification with explanation. Classify emails as 'important', 'spam', or 'casual'.",
            backstory='You are an expert email analyst who provides detailed classifications and explanations. You analyze emails to determine their category.',
            llm=MODEL_NAME,
            verbose=True
        )

        responder = Agent(
            role='Email Responder',
            goal='Create detailed and appropriate responses based on email classification',
            backstory='You are an expert at crafting detailed, appropriate responses.',
            llm=MODEL_NAME,
            verbose=True
        )

        organizer = Agent(
            role='Organizer',
            goal='Ensure thorough analysis and appropriate responses',
            backstory='You review classifications and responses to ensure completeness.',
            llm=MODEL_NAME,
            verbose=True
        )

        # Create tasks
        tasks = [
            Task(
                description=f"Analyze this email in detail: '{email}'\n1. Determine if it's spam, important, or casual\n2. Explain why\n3. List suspicious elements\n4. Provide risk assessment",
                agent=classifier,
                expected_output="Detailed classification report"
            ),
            Task(
                description=f"Based on the classification of: '{email}'\n1. Create appropriate response\n2. Explain why\n3. Include warnings\n4. Suggest follow-ups",
                agent=responder,
                expected_output="Complete response strategy"
            ),
            Task(
                description="Review the classification and response\n1. Verify classification return if the classification is 'important', 'spam', or casual\n2. Confirm response\n3. Add recommendations\n4. Provide summary",
                agent=organizer,
                expected_output="Comprehensive review"
            )
        ]

        return [classifier, responder, organizer], tasks

    except Exception as e:
        print("Error in agent creation:", str(e))
        traceback.print_exc()
        raise Exception("Failed to create agents and tasks")

@app.route('/connect-gmail', methods=['GET'])
def connect_gmail():
    """Initialize Gmail connection and return authorization URL"""
    try:
        auth_url = gmail_service.get_authorization_url()
        return jsonify({'auth_url': auth_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/gmail-callback', methods=['GET'])
def gmail_callback():
    """Handle Gmail OAuth callback"""
    try:
        code = request.args.get('code')
        gmail_service.handle_callback(code)
        return jsonify({'message': 'Gmail connected successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-gmail', methods=['GET'])
def analyze_gmail():
    """Analyze unread emails in Gmail"""
    try:
        results = gmail_service.process_unread_emails(create_agents_and_tasks)
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze_email():
    """Analyze an email by classifying it, generating a response, and reviewing it"""
    try:
        data = request.get_json()
        print("Received request data:", data)  # Debugging input
        
        email = data.get('email')
        if not email:
            return jsonify({'error': 'No email provided'}), 400

        agents, tasks = create_agents_and_tasks(email)
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

        # Debugging Crew execution
        try:
            print("Starting Crew execution...")
            result = crew.kickoff()
            print("Crew Result:", result)
        except Exception as e:
            print("Error during Crew execution:", str(e))
            traceback.print_exc()
            return jsonify({'error': 'Error during Crew execution: ' + str(e)}), 500

        # Ensure the result is JSON serializable
        if isinstance(result, dict):
            return jsonify({'result': result})
        elif isinstance(result, list):
            return jsonify({'result': [str(item) for item in result]})
        else:
            return jsonify({'result': str(result)})

    except Exception as e:
        print("Server error:", str(e))
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
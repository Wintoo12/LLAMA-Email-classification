from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText
import json
import traceback

class GmailService:
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self):
        self.service = None
        self.credentials = None

    def get_authorization_url(self):
        """Generate Gmail authorization URL"""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', 
                self.SCOPES,
                redirect_uri='http://localhost:5000/gmail-callback'
            )
            auth_url, _ = flow.authorization_url(access_type='offline')
            return auth_url
        except Exception as e:
            print(f"Error generating authorization URL: {str(e)}")
            traceback.print_exc()
            raise

    def handle_callback(self, code):
        """Handle OAuth callback and initialize Gmail service"""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                self.SCOPES,
                redirect_uri='http://localhost:5000/gmail-callback'
            )
            flow.fetch_token(code=code)
            self.credentials = flow.credentials
            self.service = build('gmail', 'v1', credentials=self.credentials)
        except Exception as e:
            print(f"Error handling callback: {str(e)}")
            traceback.print_exc()
            raise

    def get_email_content(self, msg_data):
        """Extract email content from Gmail message"""
        try:
            payload = msg_data['payload']
            
            # Handle multipart messages
            if 'parts' in payload:
                parts = payload['parts']
                content = ""
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            content += base64.urlsafe_b64decode(data).decode()
                return content
            
            # Handle simple messages
            if 'body' in payload and 'data' in payload['body']:
                return base64.urlsafe_b64decode(payload['body']['data']).decode()
            
            # Handle messages with nested parts
            def extract_from_parts(parts):
                content = ""
                for part in parts:
                    if 'parts' in part:
                        content += extract_from_parts(part['parts'])
                    elif part.get('mimeType') == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            content += base64.urlsafe_b64decode(data).decode()
                return content

            if 'parts' in payload:
                return extract_from_parts(payload['parts'])
            
            return "Could not extract email content"
            
        except Exception as e:
            print(f"Error extracting email content: {str(e)}")
            traceback.print_exc()
            return f"Error: {str(e)}"

    def process_unread_emails(self, create_agents_and_tasks):
        """Process all unread emails"""
        if not self.service:
            raise Exception("Gmail service not initialized. Please connect first.")

        try:
            results = []
            messages = self.service.users().messages().list(
                userId='me', 
                labelIds=['INBOX'], 
                q="is:unread"
            ).execute().get('messages', [])

            for message in messages:
                try:
                    # Get full message data
                    msg_data = self.service.users().messages().get(
                        userId='me', 
                        id=message['id']
                    ).execute()
                    
                    # Extract email content
                    email_content = self.get_email_content(msg_data)
                    
                    # Get email metadata
                    headers = msg_data['payload']['headers']
                    subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
                    sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown Sender')
                    
                    # Analyze email using CrewAI
                    agents, tasks = create_agents_and_tasks(email_content)
                    crew = Crew(
                        agents=agents,
                        tasks=tasks,
                        process=Process.sequential,
                        verbose=True
                    )
                    analysis_result = crew.kickoff()
                    
                    # Store results
                    results.append({
                        'message_id': message['id'],
                        'subject': subject,
                        'sender': sender,
                        'content': email_content,
                        'analysis': analysis_result
                    })
                    
                    # Mark as read
                    self.service.users().messages().modify(
                        userId='me',
                        id=message['id'],
                        body={'removeLabelIds': ['UNREAD']}
                    ).execute()
                    
                except Exception as e:
                    print(f"Error processing message {message['id']}: {str(e)}")
                    traceback.print_exc()
                    results.append({
                        'message_id': message['id'],
                        'error': str(e)
                    })

            return results

        except Exception as e:
            print(f"Error processing unread emails: {str(e)}")
            traceback.print_exc()
            raise
import sys
import os
from autogen import GroupChat, GroupChatManager, AssistantAgent, UserProxyAgent
from serpapi import GoogleSearch
import schedule
import time
import serpapi
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
load_dotenv()
sys.path.append(os.path.abspath("."))
API_KEY = os.getenv("SERPAPI_KEY")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import fitz  
import docx
from serpapi import GoogleSearch
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

filePath = r"D:\autogen_leaning\autogen_tutorial\Project-Autogen\Job_Advisor\Backend_Lalitha_Resume.pdf"
llm_config={
    "config_list": [
        {
            'model': "gpt-4o-mini",
            'api_key':os.getenv("API_KEY"),
            'base_url': os.getenv("BASE_URL"),
            'api_type': "azure",
            'api_version': "2024-12-01-preview",
            'tags': ['tool', 'gpt-4o-mini'],          
        }
    ]
}

def search_linkedin_jobs(role: str, experience: str, location: str) -> list:
    """Search LinkedIn for jobs dynamically using role & experience from agent (posted in last 24 hours)."""
    print("=" * 50)
    print("TOOL CALLED: search_linkedin_jobs")
    print(f"Searching LinkedIn jobs for: {role} ({experience}) in {location}")
    print("Filter: Last 24 hours only (LinkedIn direct search URL)")
    print("=" * 50)

    try:
        base_url = "https://www.linkedin.com/jobs/search/"
        query_params = (
            f"?keywords={role.replace(' ', '+')}+{experience.replace(' ', '+')}"
            f"&location={location.replace(' ', '+')}&f_TPR=r86400"
        )
        linkedin_url = base_url + query_params

        job_entry = {
            "title": f"{role} Jobs ({experience}) - {location}",
            "company": "LinkedIn Jobs",
            "link": linkedin_url,
            "description": (
                "Click the link below to view all recent LinkedIn job postings "
                "matching this role and experience level (posted in the last 24 hours)."
            )
        }

        print(f" LinkedIn Search URL: {linkedin_url}\n")
        print(" Dynamic LinkedIn search built successfully.\n")
        return [job_entry]

    except Exception as e:
        print(f"Error searching jobs: {e}")
        print(f"Error type: {type(e).__name__}")
        return []

def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """Send an HTML email using Gmail SMTP + App Password."""
    print("=" * 50)
    print("TOOL CALLED: send_email_notification")
    print(f"Sending email to: {to_email}")
    print(f"Subject: {subject}")
    print(f"From: {EMAIL}")
    print("=" * 50)

    try:
        msg = MIMEText(body, "html", "utf-8")
        msg["Subject"] = subject
        msg["From"] = EMAIL
        msg["To"] = to_email

        print("Connecting securely to Gmail SMTP...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:  # SSL avoids EHLO/TLS steps
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, to_email, msg.as_string())

        print(f" Email successfully sent to {to_email}")
        print("=" * 50)
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(" Authentication failed — likely wrong email or App Password.")
        print(e)
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
        return False
    except Exception as e:
        print(f" General error: {e}")
        return False



# Create specialized agents
resume_analyzer = AssistantAgent(
    name="ResumeAnalyzer",
    system_message="""You are a resume analysis expert. Your role is to:
    1. Analyze the user's resume/CV content
    2. Extract key skills, experience, and qualifications
    3. Identify the user's experience level (entry, 1-2 years, 2-3 years, 3-5 years, 5+ years)
    4. Determine relevant job titles and industries based on skills and experience
    5. Provide the job roles and experience level to the job searcher agent
    6. Format your response EXACTLY as: "Job Role: [specific_role], Experience Level: [experience_level]"
    7. Be specific with job roles (e.g., "Software Engineer", "Data Scientist", "Frontend Developer")
    8. Focus on jobs posted in the last 24 hours only
    
    Example output: "Job Role: Software Engineer, Experience Level: 1-2 years"
    """,
    llm_config=llm_config
)

job_searcher = AssistantAgent(
    name="JobSearcher", 
    system_message="""You are a job search specialist. Your role is to:
    You will receive job roles and experience level from the resume analyzer agent.
    1. Extract the job role and experience level from the ResumeAnalyzer's response
    2. Use the search_linkedin_jobs function to find relevant job opportunities
    3. Call search_linkedin_jobs with the extracted role, experience level, and location="India"
    4. The function will return multiple jobs (up to 10) that match the user's experience level
    5. Process the returned job data and present it in a structured format
    6. Include job titles, companies, URLs, and match scores in your response
    7. Focus on jobs with strong to medium match based on experience level
    8. Return all matching jobs, not just a single job
    
    IMPORTANT: Do not hardcode any parameters. Extract role and experience from the previous agent's response.
    """,
    
    llm_config=llm_config
)

# Register the tool with the assistant agent
job_searcher.register_for_llm(name="search_linkedin_jobs", description="Search for job opportunities on LinkedIn using SerpAPI")(search_linkedin_jobs)

email_notifier = AssistantAgent(
    name="EmailNotifier",
    system_message="""You are an email notification specialist. Your role is to:
    1. Take job recommendations from JobSearcher
    2. Use the send_email_notification function to send email notifications
    3. Format the job information into a proper HTML email body
    4. Create a subject line like "Your Job Recommendations !"
    5. Include job titles, companies, URLs, and match scores in the email
    6. Call send_email_notification with the user email, subject, and formatted HTML body
    7. Confirm successful email delivery
    
    Format the email body as HTML with proper structure including job titles, companies, URLs, and match scores.""",
    llm_config=llm_config
)

# Register the tool with the assistant agent
email_notifier.register_for_llm(name="send_email_notification", description="Send email notification with job recommendations to user")(send_email_notification)

# User proxy agent with Docker disabled
user = UserProxyAgent(
    name="User", 
    human_input_mode="NEVER",
    code_execution_config={"use_docker": False}
)

# Register tools with user proxy for execution
user.register_for_execution(name="search_linkedin_jobs")(search_linkedin_jobs)
user.register_for_execution(name="send_email_notification")(send_email_notification)

# Group chat setup with round robin
group_chat = GroupChat(
    agents=[user, resume_analyzer, job_searcher, email_notifier],
    messages=[],
    max_round=8
)

group_chat.agent_selection_method = "round_robin"

# Chat manager
chat_manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=llm_config,
    human_input_mode="NEVER"
)


def extract_resume_text(file_path: str) -> str:
    """Extract plain text from a PDF or DOCX resume."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f" Resume file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".pdf":
        print(f"Extracting text from PDF: {file_path}")
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text("text")

    elif ext == ".docx":
        print(f" Extracting text from DOCX: {file_path}")
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    else:
        raise ValueError("Unsupported file format. Please upload a PDF or DOCX resume.")

    print(f"Extracted {len(text.split())} words from resume.")
    return text.strip()

if __name__ == "__main__":
    resume_content = extract_resume_text(filePath)
    
    user.initiate_chat(
        chat_manager, 
        message=f"""Please analyze this resume and find relevant job opportunities:

{resume_content}

User email: chinthalalitha2004@gmail.com
Preferred location: India


Please analyze the resume, search for job opportunities, and send email notifications with the results.
"""
    )




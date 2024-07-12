import base64
import json
import requests
from github import Github
import os

# Configuration
DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')
GITHUB_ACCESS_TOKEN = os.getenv('GH_ACCESS_TOKEN')
GITHUB_REPO = 'YOUR_GITHUB_USERNAME/rss-feed'
GITHUB_FILE_PATH = 'feed.xml'  # Adjust if your feed XML file has a different name

def create_dropbox_shared_link(file_path):
    url = "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
    headers = {
        "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "path": file_path,
        "settings": {"requested_visibility": "public"}
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['url']

def get_github_file_content(repo, file_path):
    file = repo.get_contents(file_path)
    content = base64.b64decode(file.content).decode('utf-8')
    sha = file.sha
    return content, sha

def update_github_file(repo, file_path, content, sha, commit_message):
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    repo.update_file(file_path, commit_message, encoded_content, sha)

def main():
    # Initialize GitHub client
    g = Github(GITHUB_ACCESS_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    
    # Dropbox file path (ensure the correct path is provided)
    dropbox_file_path = '/path/to/your/file.mp3'
    
    # Create Dropbox shared link
    shared_link = create_dropbox_shared_link(dropbox_file_path)
    print(f"Created Dropbox shared link: {shared_link}")
    
    # Get current RSS feed content from GitHub
    rss_content, sha = get_github_file_content(repo, GITHUB_FILE_PATH)
    
    # Create new RSS item
    new_item = f"""
    <item>
        <title>New Recording</title>
        <link>{shared_link}</link>
        <description>New recording added to the RSS feed.</description>
    </item>
    """
    
    # Insert new item into RSS feed content
    updated_rss_content = rss_content.replace('</channel>', new_item + '\n</channel>')
    
    # Update RSS feed on GitHub
    update_github_file(repo, GITHUB_FILE_PATH, updated_rss_content, sha, "Added new recording to RSS feed")
    print("Updated RSS feed on GitHub.")

if __name__ == "__main__":
    main()

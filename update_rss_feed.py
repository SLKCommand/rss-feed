import base64
import json
import requests
from github import Github
import os

# Configuration
DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')
GITHUB_ACCESS_TOKEN = os.getenv('GH_ACCESS_TOKEN')
GITHUB_REPO = 'SLKCommand/rss-feed'
GITHUB_FILE_PATH = 'feed.xml'  # Adjust if your feed XML file has a different name
DROPBOX_FOLDER_PATH = '/MB/'  # Path to the folder in your Dropbox

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

def extract_info_from_filename(file_name):
    parts = file_name.split(' ')
    volume = parts[0]
    page = parts[1]
    siman = parts[2].split(':')[0]
    seif = parts[2].split(':')[1]
    title = ' '.join(parts[3:]).replace('.mp3', '')
    return volume, page, siman, seif, title

def list_files_in_dropbox_folder(folder_path):
    url = "https://api.dropboxapi.com/2/files/list_folder"
    headers = {
        "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "path": folder_path,
        "recursive": False
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['entries']

def main():
    # Initialize GitHub client
    g = Github(GITHUB_ACCESS_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    
    # List files in Dropbox folder
    files = list_files_in_dropbox_folder(DROPBOX_FOLDER_PATH)
    
    # Process each file
    for file in files:
        file_path = file['path_display']
        file_name = file['name']
        
        # Extract detailed information from file name
        volume, page, siman, seif, title = extract_info_from_filename(file_name)
        
        # Create Dropbox shared link
        shared_link = create_dropbox_shared_link(file_path)
        print(f"Created Dropbox shared link: {shared_link}")
        
        # Get current RSS feed content from GitHub
        rss_content, sha = get_github_file_content(repo, GITHUB_FILE_PATH)
        
        # Create new RSS item
        new_item = f"""
        <item>
            <title>{title}</title>
            <link>{shared_link}</link>
            <description>Volume: {volume}, Page: {page}, Siman: {siman}, Seif: {seif}</description>
        </item>
        """
        
        # Insert new item into RSS feed content
        updated_rss_content = rss_content.replace('</channel>', new_item + '\n</channel>')
        
        # Update RSS feed on GitHub
        update_github_file(repo, GITHUB_FILE_PATH, updated_rss_content, sha, "Added new recording to RSS feed")
        print("Updated RSS feed on GitHub.")

if __name__ == "__main__":
    main()

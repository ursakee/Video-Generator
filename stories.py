import os
import json
from fuzzywuzzy import fuzz
import string
import re
import html
import requests

# Define paths to the two main folders
folder1_path = './stories'
folder2_path = './done'

# Define the dictionary of words to be replaced
replacement_dict = {
    "TIFU": "Today i screwed up",
    "AITA": "Am i wrong",
    "AITAH": "Am i wrong",
    "fucked": "screwed up",
    "butthole": "rear end",
    "bitch": "mean",
    "tits": "chest",
    "blowjobs": "oral sex",
    "handjobs": "manual stimulation",
    "masturbation": "self-pleasure",
    "IMO": "In my opinion",
    "IMHO": "In my humble opinion",
    "IIRC": "If I remember correctly",
    "OP": "Original poster",
    "YTA": "You're the jerk",
    "NTA": "Not the jerk",
    "ESH": "Everyone sucks here",
    "NAH": "No jerks here",
    "FML": "Screw my life",
    "IDK": "I don't know",
    "FYI": "For your information",
    "TBT": "Throwback Thursday",
    "TIL": "Today I learned",
    "BFF": "Best friends forever",
    "SO": "Significant other",
    "MIL": "Mother-in-law",
    "FIL": "Father-in-law",
    "SIL": "Sister-in-law",
    "BIL": "Brother-in-law",
    "GF": "Girlfriend",
    "BF": "Boyfriend",
    "DH": "Dear husband",
    "DW": "Dear wife",
    "DS": "Dear son",
    "DD": "Dear daughter",
    "JNMIL": "Just no mother-in-law",
    "JNFIL": "Just no father-in-law",
    "JNSO": "Just no significant other",
    "SMH": "Shaking my head",
    "LPT": "Life pro tip",
    "AMA": "Ask me anything",
    "DIL": "Daughter-in-law",
    "AFAIK": "As far as I know",
    "TMI": "Too much information",
    "IRL": "In real life",
    "YOLO": "You only live once",
    "FOMO": "Fear of missing out",
    "BRB": "Be right back",
    "OMW": "On my way",
    "ROFL": "Rolling on the floor laughing",
    "TBH": "To be honest",
    "HMU": "Hit me up",
    "ICYMI": "In case you missed it",
    "POTD": "Post of the day",
    "LMK": "Let me know",
    "dildo": "toy",
    "penis": "private parts",
    "fuck": "f"
}

def list_subfolders(directory):
    """Return a list of subfolder names in the given directory."""
    try:
        entries = os.listdir(directory)
        subfolders = [entry for entry in entries if os.path.isdir(os.path.join(directory, entry))]
        return subfolders
    except FileNotFoundError:
        return []

def get_post_titles_and_texts(json_path):
    """Return a list of post titles and selftexts from the JSON file, skipping those with images or short stories."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    posts = []
    for subreddit in data:
        for post in data[subreddit]['data']['children']:
            if 'media_metadata' in post['data'] or 'preview' in post['data']:
                continue  # Skip posts with images
            title = post['data']['title']
            selftext = post['data'].get('selftext', '')
            if len(selftext) < 1200:
                continue  # Skip posts with selftext less than 1200 characters
            posts.append((title, selftext))
    return posts

def is_approx_match(title, subfolder, threshold=95):
    """Check if the title matches the subfolder name approximately by the given threshold."""
    return fuzz.ratio(title, subfolder) >= threshold

def ensure_punctuation(title):
    """Ensure the title ends with a punctuation mark."""
    if title[-1] not in string.punctuation:
        title += '.'
    return title

def clean_text(text):
    """Replace newlines with spaces and replace words based on the replacement dictionary."""
    # Decode HTML entities
    text = html.unescape(text)
    # Replace newlines with spaces
    text = text.replace('\n\n', ' ').replace('\n', ' ')
    # Replace words based on the replacement dictionary
    for word, replacement in replacement_dict.items():
        text = text.replace(word, replacement)
    return text

def sanitize_folder_name(name):
    """Sanitize the folder name by removing invalid characters and trimming trailing spaces and periods."""
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    # Trim trailing spaces and periods
    sanitized = sanitized.rstrip(' .')
    return sanitized


def create_story_folder_and_file(base_path, title, story_text):
    """Create a subfolder for the title and write the story to story.txt."""
    folder_name = sanitize_folder_name(title[:100])  # Limit folder name length to avoid filesystem issues
    folder_path = os.path.join(base_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, 'story.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"{clean_text(title)} {story_text}")

def get_top_posts(subreddit, base_url, params, headers):
    """Fetch top posts from a subreddit."""
    url = base_url.format(subreddit)
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for {subreddit}, status code: {response.status_code}")
        return None

def main():
    # List all subfolders in the given directories
    combined_subfolders = list_subfolders(folder1_path) + list_subfolders(folder2_path)

    # Preselected subreddits
    subreddits = ["tifu", "AmItheAsshole", "relationship_advice", "pettyrevenge", "weddingshaming", "MaliciousCompliance"]
    base_url = 'https://www.reddit.com/r/{}/top.json'
    params = {
        'sort': 'top',
        't': 'month',
        'limit': 40
    }
    headers = {'User-Agent': 'Mozilla/5.0'}

    # Fetching top posts for each subreddit
    results = {}
    for subreddit in subreddits:
        data = get_top_posts(subreddit, base_url, params, headers)
        if data:
            results[subreddit] = data

    # Save results to a JSON file
    with open('top_posts.json', 'w') as f:
        json.dump(results, f, indent=4)

    # Get post titles and selftexts from the JSON file
    posts = get_post_titles_and_texts('top_posts.json')

    # Process and clean posts
    titles_not_in_subfolders = []
    for title, selftext in posts:
        cleaned_title = ensure_punctuation(title)
        cleaned_text = clean_text(selftext)
        if not any(is_approx_match(cleaned_title, subfolder) for subfolder in combined_subfolders):
            titles_not_in_subfolders.append((cleaned_title, cleaned_text))

    # Create subfolders and story.txt files for unmatched titles
    for title, selftext in titles_not_in_subfolders:
        create_story_folder_and_file(folder1_path, title, selftext)

    print("Subfolders and story.txt files have been created for unmatched titles.")

if __name__ == "__main__":
    main()
import requests
import base64
import os
import argparse
import json

#
# --- HOW TO GET YOUR API KEYS ---
#
# 1. Serp API Key:
#    - Go to https://serpapi.com/
#    - Sign up for a free account.
#    - You will find your API key in your account dashboard.
#
# 2. Imgur Client ID:
#    - Go to https://api.imgur.com/oauth2/addclient
#    - Register a new application.
#    - Choose 'Anonymous usage without user authorization'.
#    - After registration, you will get a 'Client ID'.
#

def upload_to_imgur(client_id, image_path):
    """
    Uploads an image to Imgur and returns the direct link.
    """
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {client_id}"}

    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data)
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"Error reading or encoding image: {e}")
        return None

    payload = {
        'image': base64_image,
        'type': 'base64',
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        
        response_data = response.json()
        if response_data['success']:
            image_link = response_data['data']['link']
            print(f"Image uploaded successfully to Imgur: {image_link}")
            return image_link
        else:
            print(f"Imgur API Error: {response_data['data']['error']}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request to Imgur failed: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Failed to decode JSON response from Imgur: {response.text}")
        return None

def reverse_image_search(api_key, image_url):
    """
    Performs a reverse image search using Serp API.
    """
    params = {
        "engine": "google_reverse_image",
        "image_url": image_url,
        "api_key": api_key,
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request to Serp API failed: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Failed to decode JSON response from Serp API: {response.text}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Perform a reverse image search using Serp API and Imgur.")
    parser.add_argument("image_path", help="Path to the local image file.")
    parser.add_argument("--serp_api_key", help="Your Serp API key.", default=os.environ.get("SERP_API_KEY"))
    parser.add_argument("--imgur_client_id", help="Your Imgur client ID.", default=os.environ.get("IMGUR_CLIENT_ID"))
    args = parser.parse_args()

    if not args.serp_api_key:
        print("Error: Serp API key not provided. Use --serp_api_key or set SERP_API_KEY environment variable.")
        return
    if not args.imgur_client_id:
        print("Error: Imgur client ID not provided. Use --imgur_client_id or set IMGUR_CLIENT_ID environment variable.")
        return

    imgur_url = upload_to_imgur(args.imgur_client_id, args.image_path)

    if imgur_url:
        print("\nPerforming reverse image search...")
        results = reverse_image_search(args.serp_api_key, imgur_url)
        
        if results and "image_results" in results:
            print("\n--- Reverse Image Search Results ---")
            for result in results["image_results"]:
                print(f"Title: {result.get('title')}")
                print(f"Link: {result.get('link')}")
                print(f"Source: {result.get('source')}")
                print("-" * 20)
        else:
            print("No image results found.")

if __name__ == "__main__":
    main()

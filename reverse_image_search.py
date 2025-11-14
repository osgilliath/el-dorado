import requests
import base64
import os
import argparse
import json
import tkinter as tk
from tkinter import filedialog

#
# --- HOW TO GET YOUR API KEYS ---
#
# 1. Serp API Key:
#    - Go to https://serpapi.com/
#    - Sign up for a free account.
#    - You will find your API key in your account dashboard.
#
# 2. ImgBB API Key:
#    - Go to https://api.imgbb.com/
#    - Sign up for a free account.
#    - You will find your API key on the API page.
#

def upload_to_imgbb(api_key, image_path):
    """
    Uploads an image to ImgBB and returns the direct link.
    """
    url = "https://api.imgbb.com/1/upload"
    
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
        'key': api_key,
        'image': base64_image,
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        response_data = response.json()
        if response_data['success']:
            image_link = response_data['data']['url']
            print(f"Image uploaded successfully to ImgBB: {image_link}")
            return image_link
        else:
            print(f"ImgBB API Error: {response_data['error']['message']}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request to ImgBB failed: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Failed to decode JSON response from ImgBB: {response.text}")
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
    parser = argparse.ArgumentParser(description="Perform a reverse image search using Serp API and ImgBB.")
    parser.add_argument("--serp_api_key", help="Your Serp API key.", default=os.environ.get("SERP_API_KEY"))
    parser.add_argument("--imgbb_api_key", help="Your ImgBB API key.", default=os.environ.get("IMGBB_API_KEY"))
    args = parser.parse_args()

    if not args.serp_api_key:
        print("Error: Serp API key not provided. Use --serp_api_key or set SERP_API_KEY environment variable.")
        return
    if not args.imgbb_api_key:
        print("Error: ImgBB API key not provided. Use --imgbb_api_key or set IMGBB_API_KEY environment variable.")
        return

    # Create a Tkinter root window and hide it
    root = tk.Tk()
    root.withdraw()

    image_path = filedialog.askopenfilename(
        title="Select an Image File",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"), ("All files", "*.*")]
    )

    if not image_path:
        print("No image file selected. Exiting.")
        return

    imgbb_url = upload_to_imgbb(args.imgbb_api_key, image_path)

    if imgbb_url:
        print("\nPerforming reverse image search...")
        results = reverse_image_search(args.serp_api_key, imgbb_url)
        
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

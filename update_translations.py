import re
import json

updates_en = {
    'navAll': 'All-in-One', 'navIg': 'Instagram Reel', 'navTt': 'TikTok', 'navSnap': 'Snapchat',
    'igTitle': 'Instagram Video Downloader', 'igSub': 'Download Instagram Reels, Stories & Photos.',
    'ttTitle': 'TikTok Video Downloader', 'ttSub': 'Download TikTok Videos without watermark.',
    'snapTitle': 'Snapchat Video Downloader', 'snapSub': 'Download Snapchat Spotlight & Stories.',
    'seoHeader': 'How to Download Videos',
    'step1Title': 'Copy the Link', 'step1Desc': 'Find the video you want to download and copy its URL.',
    'step2Title': 'Paste & Select', 'step2Desc': 'Paste the link into the input box above and choose format.',
    'step3Title': 'Download Instantly', 'step3Desc': 'Hit download and save securely directly to your device.',
    'seoFooterText': 'Our free, fast, and secure video downloader supports major platforms. No login required.'
}

# we will just apply english to all for the newly added keys to ensure no JS errors
with open("static/translations.js", "r", encoding="utf-8") as f:
    content = f.read()

def repl(m):
    orig = m.group(1) 
    new_lines = []
    for k, v in updates_en.items():
        new_lines.append(f'        {k}: "{v}"')
    return orig + ",\n" + ",\n".join(new_lines)

new_content = re.sub(r'(authorUnknown:\s*"[^"]*")', repl, content)

with open("static/translations.js", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Updated translations.js successfully.")

import os
import time
import yaml
import markdown
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import subprocess

# === CONFIG ===
OBSIDIAN_DAILY_NOTES = "/Users/ignasprakapas/Documents/Life/daily_notes"
SITE_REPO = "/Users/ignasprakapas/Coding Projects/portfolio"
BLOG_INDEX_FILE = os.path.join(SITE_REPO, "blog_posts.json")
BLOG_HTML_FILE = os.path.join(SITE_REPO, "blog.html")
GIT_BRANCH = "main"
PROCESS_DELAY = 5  # seconds to wait before reading file after detection

class NewNoteHandler(FileSystemEventHandler):
    def load_blog_index(self):
        """Load existing blog posts index"""
        if os.path.exists(BLOG_INDEX_FILE):
            with open(BLOG_INDEX_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_blog_index(self, posts):
        """Save blog posts index"""
        with open(BLOG_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)

    def update_blog_html(self, posts):
        """Update the blog.html file with the latest posts"""
        # Generate HTML for blog posts with full content
        posts_html = ""
        for post in sorted(posts, key=lambda x: x.get('date', ''), reverse=True):
            # Skip posts that don't have the required fields
            if not all(key in post for key in ['title', 'date', 'html_content']):
                continue
                
            posts_html += f"""
            <article class="blog-post">
                <h2>{post['title']}</h2>
                <p class="post-date">{post['date']}</p>
                <div class="post-content">
                    {post['html_content']}
                </div>
            </article>
            <br> <br>
            """

        # Read existing blog.html template or create basic one
        if os.path.exists(BLOG_HTML_FILE):
            with open(BLOG_HTML_FILE, 'r', encoding='utf-8') as f:
                blog_content = f.read()
            
            # Replace content between markers (you'll need to add these to your blog.html)
            start_marker = "<!-- BLOG_POSTS_START -->"
            end_marker = "<!-- BLOG_POSTS_END -->"
            
            if start_marker in blog_content and end_marker in blog_content:
                before = blog_content.split(start_marker)[0]
                after = blog_content.split(end_marker)[1]
                new_content = f"{before}{start_marker}\n{posts_html}\n{end_marker}{after}"
            else:
                # If markers don't exist, append to body
                new_content = blog_content.replace("</body>", f"{posts_html}\n</body>")
        else:
            # Create basic blog.html template
            new_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>My Blog</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <h1>My Blog</h1>
    <!-- BLOG_POSTS_START -->
    {posts_html}
    <!-- BLOG_POSTS_END -->
</body>
</html>"""

        with open(BLOG_HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def process_file(self, filepath):
        time.sleep(PROCESS_DELAY)  # wait for Obsidian to finish saving
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"⚠ File {filepath} no longer exists — skipping.")
            return

        # extract YAML frontmatter if exists
        if content.startswith("---"):
            parts = content.split("---", 2)
            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2]
            title = frontmatter.get("title", os.path.basename(filepath).replace('.md', ''))
        else:
            title = os.path.basename(filepath).replace('.md', '')
            body = content

        # create excerpt from first paragraph
        excerpt = body.split('\n\n')[0][:150] + "..." if len(body) > 150 else body

        # convert to HTML
        html_body = markdown.markdown(body)
        
        # get date
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        print(f"processed post: {title}")

        # update blog index
        posts = self.load_blog_index()
        
        # create unique identifier for post (using title and date)
        post_id = f"{date_str}-{title.lower().replace(' ', '-')}"
        
        # check if post already exists (for updates) - handle both old and new formats
        existing_post = None
        for post in posts:
            # Check for new format with 'id'
            if 'id' in post and post['id'] == post_id:
                existing_post = post
                break
            # Check for old format with 'filename' (convert to new format)
            elif 'filename' in post and post.get('title') == title:
                existing_post = post
                # Convert old format to new format
                post['id'] = post_id
                if 'filename' in post:
                    del post['filename']
                if 'excerpt' in post:
                    del post['excerpt']
                break
        
        if existing_post:
            existing_post['title'] = title
            existing_post['html_content'] = html_body
            existing_post['date'] = date_str
        else:
            posts.append({
                'id': post_id,
                'title': title,
                'date': date_str,
                'html_content': html_body
            })

        self.save_blog_index(posts)
        self.update_blog_html(posts)

        # confirmation
        publish = input(f"publish '{title}' to GitHub? (y/n): ").strip().lower()
        if publish == "y":
            subprocess.run(["git", "-C", SITE_REPO, "add", "."])
            subprocess.run(["git", "-C", SITE_REPO, "commit", "-m", f"add blog post: {title}"])
            subprocess.run(["git", "-C", SITE_REPO, "push", "origin", GIT_BRANCH])
            print("post published")
        else:
            print("post saved locally, not published.")

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"new note detected: {event.src_path}")
            self.process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"note changed: {event.src_path}")
            self.process_file(event.src_path)

if __name__ == "__main__":
    event_handler = NewNoteHandler()
    observer = Observer()
    observer.schedule(event_handler, OBSIDIAN_DAILY_NOTES, recursive=False)
    observer.start()
    print("watching....")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
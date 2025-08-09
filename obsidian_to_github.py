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
BLOG_FOLDER = os.path.join(SITE_REPO, "blogs")
BLOG_INDEX_FILE = os.path.join(SITE_REPO, "blog_posts.json")
BLOG_HTML_FILE = os.path.join(SITE_REPO, "blog.html")
GIT_BRANCH = "main"
PROCESS_DELAY = 1  # seconds to wait before reading file after detection

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
        # Generate HTML for blog posts
        posts_html = ""
        for post in sorted(posts, key=lambda x: x['date'], reverse=True):
            posts_html += f"""
            <article class="blog-post">
                <h2><a href="blogs/{post['filename']}">{post['title']}</a></h2>
                <p class="post-date">{post['date']}</p>
                <p class="post-excerpt">{post.get('excerpt', '')}</p>
            </article>
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

        # wrap in basic HTML template
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <link rel="stylesheet" href="/styles.css">
    <style>
        .back-link {{ margin-bottom: 20px; }}
        .back-link a {{ text-decoration: none; color: #666; }}
        .back-link a:hover {{ color: #333; }}
    </style>
</head>
<body>
<div class="back-link">
    <a href="/blog.html">← Back to Blog</a>
</div>
<h1>{title}</h1>
{html_body}
</body>
</html>
"""
        
        # save in blog folder
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}-{title.lower().replace(' ', '-')}.html"
        output_path = os.path.join(BLOG_FOLDER, filename)

        # ensure blog folder exists
        os.makedirs(BLOG_FOLDER, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"saved post to {output_path}")

        # update blog index
        posts = self.load_blog_index()
        
        # check if post already exists (for updates)
        existing_post = next((p for p in posts if p['filename'] == filename), None)
        if existing_post:
            existing_post['title'] = title
            existing_post['excerpt'] = excerpt
        else:
            posts.append({
                'title': title,
                'filename': filename,
                'date': date_str,
                'excerpt': excerpt
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
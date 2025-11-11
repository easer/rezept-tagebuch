#!/usr/bin/env python3
"""
Simple HTTP Server for KI Code Reviews
Serves markdown files from /reviews directory
"""
from flask import Flask, render_template_string, send_from_directory
import os
from pathlib import Path
import markdown

app = Flask(__name__)
REVIEWS_DIR = Path("/reviews")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KI Code-Reviews - seaser</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .review-list {
            list-style: none;
        }
        .review-item {
            padding: 20px;
            margin-bottom: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: all 0.3s;
        }
        .review-item:hover {
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .review-item a {
            text-decoration: none;
            color: #333;
            font-size: 1.2em;
            font-weight: 500;
        }
        .review-date {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .content {
            line-height: 1.6;
            color: #333;
        }
        .content h2 { margin-top: 30px; color: #667eea; }
        .content h3 { margin-top: 20px; color: #764ba2; }
        .content pre {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
        }
        .content code {
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 4px;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        .back-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        {% if content %}
            <a href="/reviews/" class="back-link">← Zurück zur Übersicht</a>
            <div class="content">{{ content | safe }}</div>
        {% else %}
            <h1>🤖 KI Code-Reviews</h1>
            {% if reviews %}
                <ul class="review-list">
                {% for review in reviews %}
                    <li class="review-item">
                        <a href="/reviews/view/{{ review.filename }}">{{ review.title }}</a>
                        <div class="review-date">{{ review.date }}</div>
                    </li>
                {% endfor %}
                </ul>
            {% else %}
                <p>Keine Reviews gefunden.</p>
            {% endif %}
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """List all review markdown files"""
    reviews = []
    if REVIEWS_DIR.exists():
        for file in sorted(REVIEWS_DIR.glob("*.md"), reverse=True):
            reviews.append({
                'filename': file.name,
                'title': file.stem,
                'date': file.stat().st_mtime
            })

    return render_template_string(HTML_TEMPLATE, reviews=reviews, content=None)

@app.route('/view/<filename>')
def view_review(filename):
    """Display a single review markdown file"""
    file_path = REVIEWS_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        return "Review nicht gefunden", 404

    # Read and convert markdown to HTML
    with open(file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite'])

    return render_template_string(HTML_TEMPLATE, reviews=None, content=html_content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)

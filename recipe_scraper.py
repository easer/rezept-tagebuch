"""
Recipe Scraper for German Recipe Websites

Extracts recipe data from HTML pages using pattern matching and HTML parsing.
Works without external AI APIs - uses intelligent pattern recognition.
"""

import re
import json
from html.parser import HTMLParser
from html import unescape


class RecipeHTMLParser(HTMLParser):
    """Parse HTML and extract recipe-relevant content"""

    def __init__(self):
        super().__init__()
        self.title = None
        self.current_tag = None
        self.current_text = []
        self.all_text = []

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_data(self, data):
        text = data.strip()
        if text:
            self.all_text.append(text)

            # Detect title from h1/h2
            if self.current_tag in ['h1', 'h2'] and not self.title and len(text) > 5:
                self.title = text


def extract_json_ld_recipe(html):
    """
    Try to extract Schema.org Recipe data from JSON-LD

    Returns:
        dict or None: Recipe data if found
    """
    json_ld_pattern = r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>'
    matches = re.findall(json_ld_pattern, html, re.DOTALL | re.IGNORECASE)

    for match in matches:
        try:
            data = json.loads(match.strip())

            # Handle @graph format
            items = data.get('@graph', [data])

            for item in items:
                if item.get('@type') == 'Recipe':
                    # Extract recipe data
                    recipe = {
                        'title': item.get('name'),
                        'description': item.get('description'),
                        'image': extract_image_url(item.get('image')),
                        'prep_time': item.get('prepTime'),
                        'cook_time': item.get('cookTime'),
                        'total_time': item.get('totalTime'),
                        'servings': item.get('recipeYield'),
                        'ingredients': item.get('recipeIngredient', []),
                        'instructions': extract_instructions(item.get('recipeInstructions', [])),
                        'rating': extract_rating(item.get('aggregateRating')),
                        'source': 'schema.org'
                    }
                    return recipe
        except (json.JSONDecodeError, AttributeError):
            continue

    return None


def extract_image_url(image_data):
    """Extract image URL from various formats"""
    if isinstance(image_data, str):
        return image_data
    elif isinstance(image_data, dict):
        return image_data.get('url', image_data.get('@url'))
    elif isinstance(image_data, list) and image_data:
        return extract_image_url(image_data[0])
    return None


def extract_instructions(instructions_data):
    """Extract instruction steps from various formats"""
    if isinstance(instructions_data, str):
        return [instructions_data]

    steps = []
    if isinstance(instructions_data, list):
        for item in instructions_data:
            if isinstance(item, str):
                steps.append(item)
            elif isinstance(item, dict):
                text = item.get('text', item.get('itemListElement', {}).get('text', ''))
                if text:
                    steps.append(text)

    return steps


def extract_rating(rating_data):
    """Extract rating value and convert to integer"""
    if isinstance(rating_data, dict):
        rating = rating_data.get('ratingValue')
        if rating:
            try:
                # Convert to int (round if float)
                return int(round(float(rating)))
            except (ValueError, TypeError):
                return None
    return None


def extract_recipe_from_text(html):
    """
    Fallback: Extract recipe from HTML using pattern matching

    This is used when no Schema.org data is found.
    """
    # Parse HTML
    parser = RecipeHTMLParser()
    try:
        parser.feed(html)
    except:
        pass

    text = ' '.join(parser.all_text)

    # Extract title
    title = parser.title
    if not title:
        # Try to find title in text
        title_match = re.search(r'^([^.!?]{10,80})', text)
        title = title_match.group(1).strip() if title_match else 'Imported Recipe'

    # Extract ingredients
    ingredients = []

    # Pattern 1: "Zutaten:" followed by list
    zutaten_match = re.search(
        r'(?:Zutaten|ZUTATEN|Ingredients)[:：]\s*(.*?)(?:Zubereitung|Anleitung|Preparation|$)',
        text,
        re.DOTALL | re.IGNORECASE
    )

    if zutaten_match:
        zutaten_text = zutaten_match.group(1)
        # Extract lines that look like ingredients
        lines = zutaten_text.split('\n')
        for line in lines:
            line = line.strip()
            # Ingredients usually have numbers/measurements
            if re.search(r'\d+\s*(g|kg|ml|l|TL|EL|Prise|Stück)', line, re.IGNORECASE):
                ingredients.append(line)
            elif line.startswith(('-', '•', '*', '–')):
                ingredients.append(line.lstrip('-•*– '))

    # Extract instructions
    instructions = []

    # Pattern: "Zubereitung:" or numbered steps
    zubereitung_match = re.search(
        r'(?:Zubereitung|Anleitung|Preparation)[:：]\s*(.*)',
        text,
        re.DOTALL | re.IGNORECASE
    )

    if zubereitung_match:
        zubereitung_text = zubereitung_match.group(1)

        # Look for numbered steps
        steps = re.findall(
            r'(?:Schritt\s+)?(\d+)[.):]\s*([^.]{20,300}\.)',
            zubereitung_text,
            re.IGNORECASE
        )

        if steps:
            for num, step_text in steps:
                instructions.append(step_text.strip())
        else:
            # No numbered steps - split by periods or newlines
            sentences = re.split(r'[.\n]+', zubereitung_text)
            for sent in sentences[:10]:  # Max 10 steps
                sent = sent.strip()
                if len(sent) > 20:  # Meaningful instruction
                    instructions.append(sent)

    # Extract time (if mentioned)
    time_match = re.search(
        r'(\d+)\s*(?:Minuten|Min|min|Stunden|Std)',
        text,
        re.IGNORECASE
    )
    total_time = time_match.group(1) if time_match else None

    # Extract servings
    servings_match = re.search(
        r'(\d+)\s*(?:Portionen|Personen|Servings)',
        text,
        re.IGNORECASE
    )
    servings = servings_match.group(1) if servings_match else None

    return {
        'title': title,
        'description': None,
        'image': None,
        'prep_time': None,
        'cook_time': None,
        'total_time': f'PT{total_time}M' if total_time else None,
        'servings': servings,
        'ingredients': ingredients,
        'instructions': instructions,
        'rating': None,
        'source': 'pattern_matching'
    }


def scrape_recipe_from_url(url, html_content=None):
    """
    Main function to scrape recipe from URL

    Args:
        url (str): Recipe URL
        html_content (str, optional): Pre-fetched HTML content

    Returns:
        dict: Extracted recipe data
    """
    import requests

    if not html_content:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html_content = response.text

    # Try Schema.org first
    recipe = extract_json_ld_recipe(html_content)

    if recipe and recipe.get('title'):
        print(f"✅ Extracted via Schema.org: {recipe['title']}")
        return recipe

    # Fallback: Pattern matching
    recipe = extract_recipe_from_text(html_content)
    print(f"⚠️ Extracted via pattern matching: {recipe['title']}")

    return recipe


def format_recipe_for_db(recipe_data, source_url=None):
    """
    Format scraped recipe data for database insertion

    Args:
        recipe_data: Scraped recipe data
        source_url: Original URL (optional)

    Returns:
        dict: Formatted data matching our DB schema
    """
    # Format instructions as SCHRITT 1, SCHRITT 2, etc.
    instructions = recipe_data.get('instructions', [])
    formatted_steps = []

    # If only 1 long instruction, try to split it intelligently
    if len(instructions) == 1 and len(instructions[0]) > 200:
        # Split by periods followed by capital letter (likely new sentence/step)
        long_text = instructions[0]

        # Try to split on sentence boundaries that look like new steps
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÄÖÜ])', long_text)

        # Group sentences into steps (max 3-4 sentences per step)
        current_step = []
        for sentence in sentences:
            current_step.append(sentence)
            # Create new step after 2-3 sentences or if step is long enough
            if len(current_step) >= 2 and len(' '.join(current_step)) > 100:
                formatted_steps.append(f"SCHRITT {len(formatted_steps)+1}\n\n{' '.join(current_step).strip()}")
                current_step = []

        # Add remaining sentences as final step
        if current_step:
            formatted_steps.append(f"SCHRITT {len(formatted_steps)+1}\n\n{' '.join(current_step).strip()}")
    else:
        # Multiple steps already exist - use them
        for i, step in enumerate(instructions, 1):
            formatted_steps.append(f"SCHRITT {i}\n\n{step.strip()}")

    formatted_instructions = "\n\n".join(formatted_steps)

    # Build notes field
    notes = formatted_instructions

    # Add ingredients section
    ingredients = recipe_data.get('ingredients', [])
    if ingredients:
        notes += "\n\nZutaten:\n"
        notes += "\n".join(f"- {ing}" for ing in ingredients)

    # Add metadata
    notes += "\n\n─────────────────────────"

    # Determine source name from URL
    source_name = "Migusto"
    if source_url:
        if 'migusto' in source_url.lower():
            source_name = "Migusto"
        elif 'chefkoch' in source_url.lower():
            source_name = "Chefkoch"
        elif 'lecker' in source_url.lower():
            source_name = "Lecker.de"
        else:
            source_name = "Web Import"

        notes += f"\n🌍 Quelle: {source_name}"
        notes += f"\n📖 URL: {source_url}"
    else:
        notes += f"\n🌍 Quelle: URL Import"

    if recipe_data.get('servings'):
        notes += f"\n👥 Portionen: {recipe_data['servings']}"

    if recipe_data.get('source'):
        notes += f"\n📋 Methode: {recipe_data['source']}"

    # Parse duration
    duration = None
    total_time = recipe_data.get('total_time', '')
    if total_time:
        # Parse ISO 8601 duration (e.g., PT30M, PT1H30M)
        time_match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?', total_time)
        if time_match:
            hours = int(time_match.group(1) or 0)
            minutes = int(time_match.group(2) or 0)
            # Convert to hours (DB stores duration in hours, not minutes)
            total_minutes = hours * 60 + minutes
            duration = total_minutes / 60.0

    return {
        'title': recipe_data.get('title', 'Imported Recipe'),
        'notes': notes,
        'image': recipe_data.get('image'),  # URL or None
        'duration': duration,
        'rating': recipe_data.get('rating'),
        'auto_imported': True
    }


if __name__ == '__main__':
    # Test with example URLs
    test_urls = [
        'https://www.lecker.de/spaghetti-carbonara-das-beste-rezept-70254.html',
    ]

    for url in test_urls:
        print(f"\n{'='*70}")
        print(f"Testing: {url}")
        print('='*70)

        try:
            recipe = scrape_recipe_from_url(url)
            formatted = format_recipe_for_db(recipe)

            print(f"\n📝 Title: {formatted['title']}")
            print(f"⏱️  Duration: {formatted['duration']} min")
            print(f"🖼️  Image: {formatted['image']}")
            print(f"\n📄 Notes Preview:\n{formatted['notes'][:500]}...")

        except Exception as e:
            print(f"❌ Error: {e}")

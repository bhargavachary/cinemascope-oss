#!/usr/bin/env python3
"""
Update README.md with entertainment library statistics and categorized content.
"""
import json
from pathlib import Path
from collections import defaultdict


def load_library(json_path):
    """Load the library data from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def calculate_stats(library):
    """Calculate statistics from the library."""
    stats = {
        'total': len(library),
        'watched': sum(1 for item in library if item['status'] == 'Watched'),
        'watching': sum(1 for item in library if item['status'] == 'Watching'),
        'plan_to_watch': sum(1 for item in library if item['status'] == 'Plan to Watch'),
        'recommended': sum(1 for item in library if item['status'] == 'Recommended'),
        'movies': sum(1 for item in library if item['type'] == 'Movie'),
        'series': sum(1 for item in library if item['type'] == 'Series'),
    }
    
    # Calculate average rating for watched items
    watched_ratings = [item['rating'] for item in library if item['status'] == 'Watched' and item['rating'] > 0]
    stats['avg_rating'] = round(sum(watched_ratings) / len(watched_ratings), 1) if watched_ratings else 0
    
    return stats


def categorize_by_status(library):
    """Categorize library items by status."""
    categories = defaultdict(list)
    for item in library:
        categories[item['status']].append(item)
    return categories


def categorize_by_type(library):
    """Categorize library items by type."""
    categories = defaultdict(list)
    for item in library:
        categories[item['type']].append(item)
    return categories


def generate_readme(library, stats):
    """Generate the README.md content."""
    readme = []
    
    # Header
    readme.append("# Entertainment Tracker")
    readme.append("")
    readme.append("My personal entertainment library - tracking movies and series I've watched or plan to watch.")
    readme.append("")
    readme.append("**My Tastes**: High-concept Sci-Fi, Gritty Noir, & Indian Regional Gems")
    readme.append("")
    
    # Statistics
    readme.append("## 📊 Statistics")
    readme.append("")
    readme.append(f"- **Total Items**: {stats['total']}")
    readme.append(f"- **Total Watched**: {stats['watched']}")
    readme.append(f"- **Currently Watching**: {stats['watching']}")
    readme.append(f"- **Plan to Watch**: {stats['plan_to_watch']}")
    readme.append(f"- **Recommended**: {stats['recommended']}")
    readme.append(f"- **Movies**: {stats['movies']}")
    readme.append(f"- **Series**: {stats['series']}")
    if stats['avg_rating'] > 0:
        readme.append(f"- **Average Rating**: {stats['avg_rating']}/10")
    readme.append("")
    
    # Categorize by status
    categories = categorize_by_status(library)
    
    # Watched section
    if 'Watched' in categories:
        readme.append("## ✅ Watched")
        readme.append("")
        for item in sorted(categories['Watched'], key=lambda x: x['rating'], reverse=True):
            tags_str = ", ".join(item['tags']) if item['tags'] else ""
            rating_str = f"⭐ {item['rating']}/10" if item['rating'] > 0 else ""
            readme.append(f"### {item['title']}")
            readme.append(f"- **Type**: {item['type']}")
            if rating_str:
                readme.append(f"- **Rating**: {rating_str}")
            if tags_str:
                readme.append(f"- **Tags**: {tags_str}")
            readme.append("")
    
    # Currently Watching section
    if 'Watching' in categories:
        readme.append("## 🎬 Currently Watching")
        readme.append("")
        for item in categories['Watching']:
            tags_str = ", ".join(item['tags']) if item['tags'] else ""
            readme.append(f"### {item['title']}")
            readme.append(f"- **Type**: {item['type']}")
            if tags_str:
                readme.append(f"- **Tags**: {tags_str}")
            readme.append("")
    
    # Recommended section
    if 'Recommended' in categories:
        readme.append("## 🌟 Recommended")
        readme.append("")
        for item in categories['Recommended']:
            tags_str = ", ".join(item['tags']) if item['tags'] else ""
            readme.append(f"### {item['title']}")
            readme.append(f"- **Type**: {item['type']}")
            if tags_str:
                readme.append(f"- **Tags**: {tags_str}")
            readme.append("")
    
    # Plan to Watch section
    if 'Plan to Watch' in categories:
        readme.append("## 📝 Plan to Watch")
        readme.append("")
        for item in categories['Plan to Watch']:
            tags_str = ", ".join(item['tags']) if item['tags'] else ""
            readme.append(f"### {item['title']}")
            readme.append(f"- **Type**: {item['type']}")
            if tags_str:
                readme.append(f"- **Tags**: {tags_str}")
            readme.append("")
    
    # Footer
    readme.append("---")
    readme.append("")
    readme.append("*This README is automatically generated from `data/library.json`*")
    readme.append("")
    
    return "\n".join(readme)


def main():
    """Main function to update README."""
    # Get paths
    base_path = Path(__file__).parent.parent
    json_path = base_path / 'data' / 'library.json'
    readme_path = base_path / 'README.md'
    
    # Load library
    library = load_library(json_path)
    
    # Calculate statistics
    stats = calculate_stats(library)
    
    # Generate README content
    readme_content = generate_readme(library, stats)
    
    # Write README
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"✅ README.md updated successfully!")
    print(f"   Total items: {stats['total']}")
    print(f"   Watched: {stats['watched']}")


if __name__ == "__main__":
    main()

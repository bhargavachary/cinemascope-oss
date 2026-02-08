#!/usr/bin/env python3
"""
Enhance library.json with new fields: imdbID, language, genres
"""
import json
import re

def infer_language(title, tags):
    """Infer language/region from title and tags"""
    tags_lower = [t.lower() for t in tags]
    
    # Check explicit language tags
    if 'malayalam' in tags_lower:
        return 'Malayalam'
    if 'tamil' in tags_lower:
        return 'Tamil'
    if 'hindi' in tags_lower:
        return 'Hindi'
    if 'telugu' in tags_lower:
        return 'Telugu'
    if 'odia' in ' '.join(tags_lower):
        return 'Odia'
    if 'kannada' in tags_lower:
        return 'Kannada'
    
    # Check title for Indian language patterns
    regional_language_titles = [
        'Kantara', 'Bison', 'Kaantha', 'Dhurandhar', 'Maranamass', 
        'Pravinkoodu Shappu', 'Kishkindha Kaandam', 'Bramayugam',
        'Maharaja', 'Drishyam', '12th Fail', '3 Idiots', 'Taare Zameen Par',
        'Daman', 'Madharaasi', 'Retro', 'Sector 36', 'Article 15',
        'Kohrra', 'Dilli Dark', 'Stolen', 'Nishaanchi', 'Haq',
        'Homebound', 'Lokah', 'Hrudayapoorvam', 'Jugnuma', 'Ponman',
        'Sarvam Maya', 'Aan Paavam Pollathathu', 'Sister Midnight',
        'Thalavara', 'Bou Buttu Bhuta', 'Ronth'
    ]
    for regional_title in regional_language_titles:
        if regional_title.lower() in title.lower():
            # Default to Hindi for generic Indian titles
            return 'Hindi'
    
    # Japanese/Anime
    if 'anime' in tags_lower or title in ['Mirai', 'Spirited Away', 'Shōgun']:
        return 'Japanese'
    
    # Default to English for international titles
    return 'English'

def extract_genres(tags):
    """Extract genre tags (max 3)"""
    genre_keywords = [
        'Action', 'Thriller', 'Drama', 'Comedy', 'Sci-Fi', 'Horror',
        'Mystery', 'Crime', 'Fantasy', 'Romance', 'Animation', 'Noir',
        'Superhero', 'Adventure', 'Epic', 'Political', 'Folk Horror',
        'Dark Comedy', 'Time Travel', 'Spy'
    ]
    
    genres = []
    for tag in tags:
        if any(genre.lower() in tag.lower() for genre in genre_keywords):
            genres.append(tag)
        elif tag in genre_keywords:
            genres.append(tag)
    
    # Limit to 3 genres
    return genres[:3]

def enhance_library():
    """Add new fields to library.json"""
    with open('data/library.json', 'r', encoding='utf-8') as f:
        library = json.load(f)
    
    for item in library:
        # Add imdbID field (initially null, will be populated via API later)
        if 'imdbID' not in item:
            item['imdbID'] = None
        
        # Infer language if not present
        if 'language' not in item:
            item['language'] = infer_language(item['title'], item.get('tags', []))
        
        # Extract genres from tags
        if 'genres' not in item:
            genres = extract_genres(item.get('tags', []))
            # If no genre found, try to infer from tags
            if not genres and item.get('tags'):
                # Use first 3 non-language tags as genres
                non_lang_tags = [t for t in item['tags'] if t.lower() not in 
                                ['malayalam', 'tamil', 'hindi', 'telugu', 'odia', 'kannada']]
                genres = non_lang_tags[:3]
            item['genres'] = genres
    
    # Write back to file
    with open('data/library.json', 'w', encoding='utf-8') as f:
        json.dump(library, f, indent=4, ensure_ascii=False)
    
    print(f"Enhanced {len(library)} entries")
    print("\nSample enhanced entries:")
    for item in library[:5]:
        print(f"  {item['title']}: language={item['language']}, genres={item['genres']}")

if __name__ == '__main__':
    enhance_library()

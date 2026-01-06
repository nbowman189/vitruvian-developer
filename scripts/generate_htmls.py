import markdown
import os
import sys
from bs4 import BeautifulSoup

def md_to_html(md_file_path, html_file_path):
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert Markdown to HTML using the 'tables' extension
    html_body_content = markdown.markdown(md_content, extensions=['tables'])

    # Post-process HTML with BeautifulSoup to group and style meal sections
    soup = BeautifulSoup(html_body_content, 'html.parser')
    
    headers = soup.find_all('h3')
    for header in headers:
        if 'Sample Meal Structure' in header.text:
            meal_cards_to_process = []
            
            # Group elements into meal cards first
            current_meal_elements = []
            for sibling in header.find_next_siblings():
                if sibling.name == 'h2' or sibling.name == 'h1' or (sibling.name == 'h3'):
                    break
                
                if sibling.name == 'p' and sibling.strong:
                    if current_meal_elements:
                        meal_card = soup.new_tag('div', **{'class': 'meal-card'})
                        for el in current_meal_elements:
                            meal_card.append(el.extract())
                        meal_cards_to_process.append(meal_card)
                        current_meal_elements = []
                    current_meal_elements.append(sibling)
                elif sibling.name:
                    current_meal_elements.append(sibling)
            
            if current_meal_elements:
                meal_card = soup.new_tag('div', **{'class': 'meal-card'})
                for el in current_meal_elements:
                    meal_card.append(el.extract())
                meal_cards_to_process.append(meal_card)

            # Process each meal card to add sub-styling
            for card in meal_cards_to_process:
                list_items = card.find_all('li')
                for li in list_items:
                    # Style sub-headings like "**Modification:**"
                    if li.strong and li.strong.text.endswith(':'):
                        li['class'] = li.get('class', []) + ['sub-heading']
                        # Unwrap the strong tag text into the li directly
                        li.strong.unwrap()
                    # Style macro lines like "*Estimated Macros...*"
                    if li.em and 'Estimated Macros' in li.em.text:
                        li['class'] = li.get('class', []) + ['macro-line']
            
            # Insert the processed cards back into the document
            current_insertion_point = header
            for card in meal_cards_to_process:
                current_insertion_point.insert_after(card)
                current_insertion_point = card
            break

    processed_html_body = str(soup)

    styled_html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{os.path.basename(md_file_path).replace('.md', '')}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 2cm;
                max-width: 18cm;
                margin-left: auto;
                margin-right: auto;
                background-color: #f9f9f9;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #2c3e50;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
                font-weight: 600;
            }}
            h1 {{ font-size: 2.2em; border-bottom: 2px solid #eee; padding-bottom: 0.3em; }}
            h2 {{ font-size: 1.8em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }}
            h3 {{ font-size: 1.4em; }}
            ul, ol {{
                padding-left: 20px;
            }}
            li {{
                margin-bottom: 0.5em;
            }}
            p {{
                margin-bottom: 1em;
            }}
            hr {{
                border: none;
                border-top: 1px solid #ccc;
                margin: 2em 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 1em;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: 600;
            }}
            .meal-card {{
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 1.5em;
                margin-bottom: 1.5em;
                background-color: #ffffff;
                box-shadow: 0 1px 4px rgba(0,0,0,0.04);
            }}
            .meal-card p:first-of-type strong {{
                font-size: 1.25em;
                color: #34495e;
            }}
            .meal-card ul {{
                list-style: none;
                padding-left: 0;
            }}
            .meal-card li.sub-heading {{
                font-weight: 600;
                color: #34495e;
                margin-top: 1em;
                margin-bottom: 0.5em;
                font-size: 1.05em;
            }}
            .meal-card li.macro-line {{
                font-style: italic;
                color: #555;
                margin-top: 1em;
                background-color: #f8f9fa;
                padding: 0.8em;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        {processed_html_body}
    </body>
    </html>
    """
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(styled_html_content)
    print(f"Successfully created HTML: {html_file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 generate_htmls.py <input_markdown_file> <output_html_file>")
        sys.exit(1)
    
    input_md = sys.argv[1]
    output_html = sys.argv[2]
    md_to_html(input_md, output_html)

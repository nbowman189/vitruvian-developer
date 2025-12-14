import markdown
from weasyprint import HTML, CSS
import os

def md_to_pdf(md_file_path, pdf_file_path):
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert Markdown to HTML
    html_content = markdown.markdown(md_content)

    # Add basic CSS for visual friendliness
    # This CSS is embedded directly into the HTML for simplicity
    styled_html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{os.path.basename(md_file_path).replace('.md', '')}</title>
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 2cm;
                max-width: 18cm;
                margin-left: auto;
                margin-right: auto;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #2c3e50;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }}
            h1 {{ font-size: 2.2em; border-bottom: 2px solid #eee; padding-bottom: 0.3em; }}
            h2 {{ font-size: 1.8em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }}
            h3 {{ font-size: 1.4em; }}
            ul, ol {{
                margin-left: 20px;
            }}
            li {{
                margin-bottom: 0.5em;
            }}
            p {{
                margin-bottom: 1em;
            }}
            strong {{
                font-weight: bold;
            }}
            em {{
                font-style: italic;
            }}
            hr {{
                border: none;
                border-top: 1px solid #ccc;
                margin: 2em 0;
            }}
            pre, code {{
                font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 0.1em 0.4em;
                font-size: 0.9em;
            }}
            pre {{
                display: block;
                padding: 1em;
                overflow-x: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 1em;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Generate PDF
    HTML(string=styled_html_content).write_pdf(pdf_file_path)
    print(f"Successfully created PDF: {pdf_file_path}")

if __name__ == "__main__":
    md_to_pdf('Full-Meal-Plan.md', 'Full-Meal-Plan.pdf')
    md_to_pdf('Shopping-List-and-Estimate.md', 'Shopping-List-and-Estimate.pdf')

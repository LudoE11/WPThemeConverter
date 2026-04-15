import sys
import shutil
import re
from pathlib import Path
from bs4 import BeautifulSoup

def execute_cli():
    should_skip_zip = '--no-zip' in sys.argv
    if should_skip_zip:
        sys.argv.remove('--no-zip')

    if len(sys.argv) != 3:
        print("Usage: python converter.py <input_directory_path> <theme_name> [--no-zip]")
        sys.exit(1)

    input_directory_path = Path(sys.argv[1])
    theme_name = sys.argv[2]
    
    output_directory_path = Path.cwd() / theme_name
    output_directory_path.mkdir(parents=True, exist_ok=True)

    generate_style_sheet(input_directory_path, output_directory_path, theme_name)
    generate_functions_php(output_directory_path)
    copy_static_assets(input_directory_path, output_directory_path)
    generate_global_header_footer(input_directory_path, output_directory_path)
    process_html_pages(input_directory_path, output_directory_path)

    if not should_skip_zip:
        shutil.make_archive(theme_name, 'zip', Path.cwd(), theme_name)
        shutil.rmtree(output_directory_path)
        print(f"Success: Theme generated at {Path.cwd() / f'{theme_name}.zip'}")
    else:
        print(f"Success: Theme generated at {output_directory_path}")

def generate_style_sheet(input_directory_path: Path, output_directory_path: Path, theme_name: str):
    style_sheet_content = f"""/*
Theme Name: {theme_name}
Description: Automated Static to WP Conversion
Version: 1.0.0
*/\n"""
    original_style_file_path = input_directory_path / 'style.css'
    if original_style_file_path.exists():
        style_sheet_content += original_style_file_path.read_text(encoding='utf-8')
        
    (output_directory_path / 'style.css').write_text(style_sheet_content, encoding='utf-8')

def generate_functions_php(output_directory_path: Path):
    functions_php_content = """<?php
function enqueue_theme_assets() {
    wp_enqueue_style('main-style', get_stylesheet_uri());
}
add_action('wp_enqueue_scripts', 'enqueue_theme_assets');
"""
    (output_directory_path / 'functions.php').write_text(functions_php_content, encoding='utf-8')

def copy_static_assets(input_directory_path: Path, output_directory_path: Path):
    allowed_root_extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif', '.ico']
    
    for item_path in input_directory_path.iterdir():
        if item_path.is_dir() and item_path.name not in ['.git', '.github', 'node_modules']:
            destination_path = output_directory_path / item_path.name
            if destination_path.exists():
                shutil.rmtree(destination_path)
            shutil.copytree(item_path, destination_path)
        elif item_path.is_file() and item_path.suffix.lower() in allowed_root_extensions and item_path.name != 'style.css':
            shutil.copy2(item_path, output_directory_path / item_path.name)

def replace_asset_paths(document_object_model: BeautifulSoup):
    for tag in document_object_model.find_all(['img', 'script', 'source']):
        if tag.has_attr('src'):
            source_path = tag['src']
            if source_path and not source_path.startswith(('http', '//', '{{WP_URI}}', 'data:')):
                tag['src'] = f"{{{{WP_URI}}}}/{source_path}"
    
    for tag in document_object_model.find_all('link'):
        if tag.has_attr('href'):
            href_path = tag['href']
            if href_path and not href_path.startswith(('http', '//', '{{WP_URI}}', 'data:')):
                tag['href'] = f"{{{{WP_URI}}}}/{href_path}"

    for tag in document_object_model.find_all('a'):
        if tag.has_attr('href'):
            href_path = tag['href']
            if href_path.endswith('.html'):
                page_slug = href_path.replace('.html', '')
                if page_slug == 'index':
                    tag['href'] = "{{WP_HOME}}"
                else:
                    tag['href'] = f"{{{{WP_PAGE_URL:{page_slug}}}}}"
            elif href_path and not href_path.startswith(('http', '//', '#', 'mailto:', 'tel:', '{{WP_URI}}')):
                tag['href'] = f"{{{{WP_URI}}}}/{href_path}"

def restore_php_tags(html_string: str) -> str:
    if not html_string:
        return ""
    html_string = html_string.replace('{{WP_URI}}', '<?php echo esc_url(get_template_directory_uri()); ?>')
    html_string = html_string.replace('{{WP_HOME}}', "<?php echo esc_url(home_url('/')); ?>")
    html_string = re.sub(
        r'\{\{WP_PAGE_URL:([^}]+)\}\}', 
        r"<?php echo esc_url(home_url('/\1')); ?>", 
        html_string
    )
    return html_string

def generate_global_header_footer(input_directory_path: Path, output_directory_path: Path):
    index_file_path = input_directory_path / 'index.html'
    if not index_file_path.exists():
        return
        
    document_object_model = BeautifulSoup(index_file_path.read_text(encoding='utf-8'), 'lxml')
    replace_asset_paths(document_object_model)
    
    head_tag = document_object_model.head
    head_content_html = restore_php_tags("".join(str(item) for item in head_tag.contents)) if head_tag else ""
    
    header_tag = document_object_model.find('header')
    header_content_html = restore_php_tags(str(header_tag)) if header_tag else ""
    
    body_tag = document_object_model.body
    body_attributes_string = ""
    if body_tag and body_tag.attrs:
        body_attributes_string = " ".join(
            f'{key}="{value}"' if not isinstance(value, list) else f'{key}="{" ".join(value)}"'
            for key, value in body_tag.attrs.items()
        )
        
    header_php_content = f"""<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    {head_content_html}
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?> {body_attributes_string}>
{header_content_html}"""
    (output_directory_path / 'header.php').write_text(header_php_content, encoding='utf-8')
    
    footer_tag = document_object_model.find('footer')
    footer_content_html = restore_php_tags(str(footer_tag)) if footer_tag else ""
    
    footer_php_content = f"""{footer_content_html}
    <?php wp_footer(); ?>
</body>
</html>"""
    (output_directory_path / 'footer.php').write_text(footer_php_content, encoding='utf-8')

def process_html_pages(input_directory_path: Path, output_directory_path: Path):
    for html_file_path in input_directory_path.glob('*.html'):
        document_object_model = BeautifulSoup(html_file_path.read_text(encoding='utf-8'), 'lxml')
        replace_asset_paths(document_object_model)
        
        has_header_tag = document_object_model.find('header') is not None
        has_footer_tag = document_object_model.find('footer') is not None
        
        if has_header_tag:
            document_object_model.find('header').decompose()
        if has_footer_tag:
            document_object_model.find('footer').decompose()
            
        body_tag = document_object_model.body
        inner_body_content_html = "".join(str(item) for item in body_tag.contents) if body_tag else str(document_object_model)
        inner_body_content_html = restore_php_tags(inner_body_content_html)
            
        file_stem_name = html_file_path.stem
        php_file_content_lines = []
        
        if file_stem_name != 'index':
            php_file_content_lines.append(f"<?php /* Template Name: {file_stem_name.capitalize()} */ ?>")
            
        if has_header_tag:
            php_file_content_lines.append("<?php get_header(); ?>")
            
        php_file_content_lines.append(inner_body_content_html.strip())
        
        if has_footer_tag:
            php_file_content_lines.append("<?php get_footer(); ?>")
            
        if file_stem_name == "index":
            (output_directory_path / "front-page.php").write_text("\n".join(php_file_content_lines), encoding='utf-8')
            (output_directory_path / "index.php").write_text("\n".join(php_file_content_lines), encoding='utf-8')
        else:
            output_filename = f"page-{file_stem_name}.php"
            (output_directory_path / output_filename).write_text("\n".join(php_file_content_lines), encoding='utf-8')

if __name__ == "__main__":
    execute_cli()
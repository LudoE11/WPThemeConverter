# HTML to WordPress Theme Converter

A fast, automated CLI utility written in Python that converts a static multi-page HTML/CSS/JS website into a structured WordPress theme. 

Instead of manually slicing HTML files, extracting headers and footers, and rewriting asset paths, this tool automates the foundational work. It generates a ready-to-install WordPress theme directory so you can immediately begin integrating dynamic WordPress features (like the Loop or custom fields).

## Features

- **Automated Slicing:** Automatically extracts `<header>` and `<footer>` tags from your `index.html` to create global `header.php` and `footer.php` files.
- **Asset Routing:** Scans for images, scripts, and stylesheets, automatically prepending them with WordPress's `get_template_directory_uri()`.
- **Internal Link Conversion:** Converts local links (e.g., `href="contact.html"`) into dynamic WordPress URL structures (`home_url('/contact')`).
- **Template Generation:** Converts every secondary `.html` file into a distinct WordPress Custom Page Template (`page-*.php`).
- **WP Hooks Injection:** Automatically injects mandatory WordPress hooks (`wp_head()`, `wp_footer()`, `body_class()`).
- **Auto-Zipping:** Compresses the generated theme directory into a `.zip` file ready for WordPress deployment.

---

## Installation

### Prerequisites
- [Python](https://www.python.org/downloads/) 3.7 or higher
- [`pip` (Python package installer)](https://pip.pypa.io/en/stable/installation)

### Setup

1. **Clone or download** this repository.
2. **Open your terminal** and navigate to the project directory.
3. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```
4. **Activate the virtual environment**:
   - **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
   - **Mac/Linux:** `source venv/bin/activate`
5. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 📂 Expected Input Structure

The tool is highly flexible and agnostic to your naming conventions. The **only strict requirement** is an `index.html` file (the home page of your site), which is used as the master template to extract your global header and footer. Everything else is completely optional and should be automatically processed if present.

```text
your-static-site/
├── index.html            # REQUIRED: Used to build header.php, footer.php, and front-page.php
├── any-other-page.html   # (Optional) Converted into a Custom WP Template (page-any-other-page.php)
├── style.css             # (Optional) Appended to the WP theme's style.css
├── script.js             # (Optional) Copied directly to the theme root
├── image.webp            # (Optional) Allowed root-level images are copied directly
└── any_folder/           # (Optional) All subdirectories (images/, assets/, css/, etc.) are copied intact
```

*Note: `<header>` and `<footer>` tags must be present in your `index.html` for them to be successfully extracted into the global WP partials.*

---

## Usage

Run the CLI tool by passing the path to your static site and the desired name for your new WordPress theme.

```bash
python converter.py "/path/to/your-static-site" "MyAwesomeTheme"
```

By default, this will process your files and generate a ready-to-upload `MyAwesomeTheme.zip` file in your current working directory.

**Options:**
If you want to inspect or modify the generated PHP files before uploading, you can bypass the automatic zipping process by appending the `--no-zip` flag. This will leave the raw theme folder unzipped instead.

```bash
python converter.py "/path/to/your-static-site" "MyAwesomeTheme" --no-zip
```

---

## WordPress Integration Guide

Once the CLI tool finishes generating your theme, follow these steps to integrate it into your WordPress installation:

### 1. Install the Theme
1. Locate the newly generated theme folder (e.g., `MyAwesomeTheme`).
2. Compress the entire folder into a `.zip` file.
3. Log in to your WordPress Admin Dashboard (`/wp-admin`).
4. Navigate to **Appearance > Themes**.
5. Click **Add Theme** at the top, then **Upload Theme**.
6. Upload your `.zip` file, install it, and click **Activate**.

Or you can manually copy the unzipped folder directly into your Wordpress directory (also works if you're using Local WP) by pasting it in `app/public/wp-content/themes`. Then activate the theme in the WP admin dashboard like mentionned above.

### 2. Set Up the Homepage
1. In the WP Dashboard, go to **Pages > Add New**.
2. Title the page "Home" (or "Accueil").
3. Leave the content blank.
4. Publish the page.
5. Go to **Settings > Reading**.
6. Under "Your homepage displays", select **A static page**.
7. Set the **Homepage** dropdown to the "Home" page you just created. Save changes. *(Because the script generated a `front-page.php`, WordPress will automatically apply your index HTML layout to this page).*

### 3. Recreate Your Subpages
For every other HTML file the script converted (e.g., `formations.html`, `contact.html`), you must create a matching page in WordPress to activate the layout.

1. Go to **Pages > Add Page**.
2. Title the page identically to the original HTML file name (e.g., "Contact"). 
3. *Crucial Step:* Look at the **Template** panel on the right sidebar. Select the dropdown and choose the template that matches your page (e.g., `Contact`).
4. Publish the page. Ensure the page "Slug" (URL) matches the original HTML file name so your links work perfectly.
5. Repeat this for all other pages.

---

## ⚠️ Limitations & Next Steps

This tool is a **scaffolding utility**, not an AI developer. It handles the tedious file structuring and asset pathing, but it does **not** make your content dynamic in the database.

**What you will still need to do manually in your PHP files:**
- Replace static text blocks with `the_content()` if you want to edit text via the Gutenberg editor.
- Implement standard WordPress Loops (`if (have_posts()) : while (have_posts()) : the_post();`) where blog feeds or dynamic lists are required.
- The tool assumes your index.html file contains your header and footer, I think this handles most common cases, but if your website has a different layout your header and footer may not get extracted correctly. Also the header and footer are automatically called on every page, again I think this is common behavior for most websites but if yours is different you may want to remove the header and footer imports manually in the relevant php files.
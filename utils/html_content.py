def generate_html_content(banner_ids, images_directory):
    html_content = """
        <html>
            <head>
                <title>Top Banners</title>
            </head>
            <body>
                <h1>Top Banners</h1>
                <div>
        """

    # Add images to HTML content
    for banner_id in banner_ids:
        html_content += f'<img src="/{images_directory}/image_{banner_id}.png" width="200" height="200"/>\n'

    html_content += """
                </div>
            </body>
        </html>
    """

    return html_content

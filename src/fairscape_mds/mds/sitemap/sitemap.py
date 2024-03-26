

sitemap_template = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {% for staticSite in static %}
    <url>
        <loc>{'https://' + domain + '/' + staticSite}</loc>
        <changefreq></changefreq>
        <priority>0.8</priority>
    </url>
    {% endfor %}
    {% for identifier in guids %}
   <url>
      <loc>{'https://' + domain + '/' + identifier.guid}</loc>
      <lastmod>{identifier.sdDatePublished}</lastmod>
      <changefreq>monthly</changefreq>
      <priority>0.5</priority>
   </url>
   {% endfor %}
</urlset> 
"""


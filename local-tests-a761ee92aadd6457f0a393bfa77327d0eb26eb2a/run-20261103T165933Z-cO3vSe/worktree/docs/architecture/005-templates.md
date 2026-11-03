## Templates

Jinja2 uses a `ChoiceLoader` with `web_html/` first, then `templates/`.
Page templates (`web_html/admin/*.html`, `web_html/viewer/*.html`) extend
`templates/base.html` and include partials from `templates/partials/`.


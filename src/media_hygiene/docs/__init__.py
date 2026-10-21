"""The documentation inside the image: rendered at build time, served at run time.

`render` (with `nav` and `rewrite`) turns `documentation/` into HTML fragments and an
index per language, with the site's own Markdown extensions; it needs the `docs`
dependency group and never runs in the shipped image. `links` is shared with the
site's MkDocs hooks; `pages` describes the index; `shelf` finds the rendered docs;
`served` gives a chapter's address, here or on the public site.
"""

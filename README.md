# Zbigniew Zabost · Senior Site Reliability Engineer

Personal page: **https://zbigniewzabost.github.io**

A single static `index.html`. The career run plays by itself (about 15 s): pipeline stages fill with the roles and skills picked up in each phase. The page names no employers. Below it are ways of working and topic hashtags. It has light and dark themes and needs no build step to host. The page makes no third-party requests: fonts and logos are embedded, so visitors' IPs go only to GitHub.

## Publish on GitHub Pages

1. Create a repository named `<your-github-user>.github.io`, or any repository with Pages enabled.
2. Commit `index.html`, `og-image.png` and `.nojekyll` to the default branch.
   Build with `python3 build.py --site-url https://<your-github-user>.github.io`, so link previews on LinkedIn or Slack get an absolute image URL.
3. Go to **Settings → Pages → Build and deployment**, choose *Deploy from a branch*, and pick the branch and `/ (root)`.

## Edit content

- Content (roles, skills, ways of working, hashtags) lives in `src/content.json`; the format is described in its `_comment` field. A skill's optional 7th field is a note shown next to its year (for example `"personal"`). Layout and behaviour live in `src/page.html`.
- Logos live in `assets/icons/tools/`. The build embeds only the ones the page refers to. Sources and licences are in [NOTICE.md](NOTICE.md).
- Rebuild after any change: `python3 build.py --site-url https://zbigniewzabost.github.io`. It inlines the content, logos and fonts into `index.html`, and writes a plain-HTML copy of the finished state for search engines and visitors without JavaScript.
- `python3 tools/og_image.py` redraws the link-preview image (needs Pillow).

## Licence

The code is MIT, and the personal content is all rights reserved; see [LICENSE](LICENSE). Third-party logos and fonts keep their own licences; see [NOTICE.md](NOTICE.md).

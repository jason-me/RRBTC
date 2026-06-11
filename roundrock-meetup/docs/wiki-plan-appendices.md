---
title: Wiki Plan — Appendices (Status, Hosting, Radicle, Open Questions)
created: 2026-06-01
updated: 2026-06-01
status: draft
---

# Wiki Plan Appendices

## Appendix A: Actual Status (as of 2026-06-01)

| Phase | Status | Notes |
|-------|--------|-------|
| 0 — Source transfer | Partial | Text files movable via MCP. Binary files (.pptx/.pdf) require base64 or manual extraction. |
| 1 — Wiki structure | DONE | Directories, SCHEMA.md, index.md, log.md, git repo all exist. |
| 2 — Admin wiki | NOT STARTED | Directory /home/agentorange/wiki/admin/ does not exist yet. |
| 3 — Ingest new slides | PARTIAL | Presentation outline exists in presentations/. Raw cheatsheet exists. Entity braiins-hashpower.md created. Missing: hashguard.md, hashrate-autopilot.md, core-vs-knots.md, and other concept pages from the new deck. |
| 4 — Tooling/code context | NOT STARTED | sovereign-digest scripts not yet referenced in wiki. |
| 5 — Website content | NOT STARTED | |
| 6 — External research | NOT STARTED | |
| 7 — Radicle publishing | STARTED BUT BLOCKED | .rad/ directory exists. Git remotes configured. rad CLI missing from agentorange. Delegate key lives on wakazashi — pushes from agentorange do not propagate to network. |
| 8 — Website publishing | NOT STARTED | |
| 9 — Obsidian sync | NOT STARTED | |
| 10 — Embeddings | NOT STARTED | |


---

## Appendix B: Radicle Publishing Reality

**The Problem**
The RoundRock-Meetup repo delegate key lives on wakazashi. Pushing `git push rad master` from agentorange updates the local git ref but **does not propagate** to the Radicle network. Other peers and the web UI still see old commits.

**Why**
Radicle's `git-remote-rad` helper only writes to node storage when the push includes the delegate's public key in the remote URL. Non-delegate pushes are silently ignored.

**The Workflow (from skill: radicle-delegate-push)**

1. **Develop on agentorange** — edit, commit, test locally.
2. **Bundle commits** on agentorange:
   ```bash
   cd /agent/files/meetup
   git bundle create /tmp/rrb-wiki.bundle master ^<last-known-common-commit>
   ```
3. **Transfer bundle to wakazashi** (via scp, rsync, or temporary HTTP server).
4. **Unbundle and delegate-push from wakazashi**:
   ```bash
   cd ~/RoundRock-Meetup
   git bundle unbundle /tmp/rrb-wiki.bundle
   git merge master
   git push rad://z3gAUxMoQvVVFYcX1qZPdo8PLAY2Q/z6MkpyMNd9HBnmTekVjmkEEhJSCPvg2YDAdDhwHNB18dvZio master --force
   ```

**Alternative: Install rad CLI on agentorange**
If the delegate key were copied to agentorange, pushes would work directly. This defeats the security model of keeping the delegate key on wakazashi. Not recommended.

**Verification**
After delegate push, check on any Radicle node:
```bash
rad ls
# Should show the repo with the new HEAD commit
```


---

## Appendix C: Website Hosting Options — Research

Goal: Members can browse wiki content in a web browser without installing anything.

### Option 1: Python Built-in HTTP Server + Custom Markdown Renderer

**What**
A Python script that:
- Walks `/agent/files/meetup/wiki/`
- Converts markdown → HTML with a dark theme
- Converts `[[wikilinks]]` → clickable relative links
- Outputs static HTML to `/agent/files/meetup/site/`
- Serves on a free port with `python3 -m http.server`

**Pros**
- Zero new dependencies. Python 3.12 already installed.
- Full control over CSS, layout, and wikilink behavior.
- Can exclude private sections (raw/, queries/, _archive/) from the public build.

**Cons**
- Single-threaded. Not suitable for high traffic (fine for a meetup wiki).
- No built-in search. Would need to add a small JS search index or rely on browser find.
- Must regenerate HTML after every edit (could be automated with a file watcher or cron).

**Effort** — Low. A 100–200 line Python script.

**Example port** — 8083 (currently free on agentorange).

---

### Option 2: mdBook

**What**
A single Rust binary that turns a directory of markdown files into a searchable static site with sidebar navigation, search, and theming.

**Pros**
- Built-in search (no JS needed).
- Great default dark theme.
- Handles relative links well.
- Used by the Rust community — proven, stable.

**Cons**
- Requires installing the `mdbook` binary (~15MB).
- Wikilinks `[[page]]` are not native mdBook syntax — would need conversion to `[page](page.html)` at build time.
- Less control over exact layout than a custom script.

**Effort** — Low–Medium. Install binary, write a small wrapper script for wikilink conversion.

---

### Option 3: MkDocs + Material Theme

**What**
A Python-based static site generator with a rich plugin ecosystem. The Material theme is widely used for documentation.

**Pros**
- Professional look out of the box.
- Plugin ecosystem (search, minification, versioning).
- Python-based — same stack as other agentorange tools.

**Cons**
- Heavier dependency tree (pip install mkdocs-material).
- Overkill for a small wiki.
- Wikilink conversion needed, same as mdBook.

**Effort** — Medium.

---

### Option 4: nginx + Static Site

**What**
Install nginx and serve pre-built static HTML from `/var/www/wiki/`.

**Pros**
- Fast, production-grade, handles concurrent connections.
- Can add TLS later with Let's Encrypt.

**Cons**
- nginx not currently installed on agentorange.
- Requires system-level config (systemd service, firewall rules).
- Still need a markdown-to-HTML generator (one of the above) to produce the static files.

**Effort** — Medium. More ops work than content work.


### Comparison Matrix

| Criterion | Python Script | mdBook | MkDocs | nginx |
|-----------|-------------|--------|--------|-------|
| Dependencies | None | 1 binary | pip + plugins | nginx + generator |
| Search | Needs custom JS | Built-in | Built-in | Depends on generator |
| Wikilink support | Native (we write it) | Needs conversion | Needs conversion | Needs conversion |
| Dark theme | Custom CSS | Built-in | Built-in | Custom CSS |
| Effort | Low | Low–Med | Medium | Medium |
| Traffic handling | Low (single-threaded) | Static files → high | Static files → high | High |
| Automation ease | Easy (cron or watcher) | Easy (build script) | Easy (build script) | Medium |

### Recommendation (pending decision)

For a meetup wiki with <50 pages and <20 concurrent readers, **Option 1 (Python script)** or **Option 2 (mdBook)** are the sweet spots. Python script gives maximum control over wikilinks and layout. mdBook gives search and navigation for free.

A hybrid is also possible: use the Python script for wikilink-aware rendering and a small JS search library like Fuse.js for client-side search.

**Next research step:** Prototype the Python script on a subset of pages (entities/ only) and evaluate output quality before committing.


---

## Appendix D: Agent Access for Content Generation

**Current state:** Any agent with MCP access to agentorange can already read wiki files via `read_file`. This means:
- Agents can query wiki content to help draft meetup talks, website copy, or social posts.
- Agents can summarize cross-page relationships (e.g., "how does DATUM relate to Stratum V2?").
- Agents cannot write to the admin wiki (Linux permissions block MCP user).

**No additional work needed** for this use case. It works today.

---

## Appendix E: Open Questions

1. **Hosting decision** — Python script, mdBook, or other? (see Appendix C)
2. **Radicle workflow automation** — Can we script the bundle → transfer → delegate-push steps to reduce manual friction?
3. **Obsidian sync direction** — Read-only pull from agentorange, or bidirectional?
4. **Admin wiki priority** — Build now, or after meetup wiki is mature?
5. **Embedding layer (Chroma/nomic)** — Phase 10 in original plan. Still desired after content exists?
6. **Contributor permissions** — Who can submit Radicle patches? Just you, or trusted members?
7. **Website domain** — Is the meetup website on agentorange (port 3000 is Open WebUI), or a separate host?

---

*This file is a supplement to the main plan at `~/wiki_setup_plan.md` on the Mac.*

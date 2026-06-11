---
title: Bitcoin Meetup Wiki — Setup, Ingestion & Publishing Plan
created: 2026-05-14
updated: 2026-06-01
status: draft
---

# Bitcoin Meetup Wiki — Setup, Ingestion & Publishing Plan

## Objective

Build two persistent, compounding knowledge bases on agentorange using the Karpathy LLM Wiki pattern:

**Meetup Wiki** — Public Bitcoin mining knowledge for the Round Rock Bitcoiners. Served via Radicle (P2P), the meetup website (browse), and Obsidian (power users). Accessible to the Hermes agent via MCP for ingestion and maintenance.

**Admin Wiki** — Private operational knowledge for you and agentorange's internal tools. Linux-isolated from MCP tools. The agent cannot reach it through normal tool calls. It exists for you and for scripts running directly on agentorange.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                    agentorange (Sovereign)                          │
│                                                                    │
│  /agent/files/meetup/wiki/          /home/agentorange/wiki/admin/   │
│  (public, MCP-readable)             (private, chmod 700,           │
│   ↑ Hermes ingests                    air-gapped from MCP)         │
│   ↑ MCP read_file works              ↑ You via SSH only            │
│   ↑ Frontier models can query)        ↑ No T3 access)              │
│                                                                    │
└──────┬─────────────────────────┬──────────────┬───────────────────┘
       │                         │              │
       ▼                         ▼              ▼
┌────────────┐         ┌────────────┐   ┌──────────────┐
│ Radicle P2P│         │ Meetup Web │   │ Mac Obsidian │
│ (clone,    │         │ (browse    │   │ (read-only   │
│  edit,     │         │  via HTTP) │   │  via rsync)  │
│  patches)  │         └────────────┘   └──────────────┘
└────────────┘                        (meetup wiki only)
```

### Key Design Decisions

1. **agentorange is canonical** — Both wikis live on the sovereign server. All ingests, writes, and maintenance happen here.

2. **Meetup wiki is MCP-accessible** — `/agent/files/meetup/wiki/` is within the MCP tool scope. The agent can read/write for ingestion and maintenance. Frontier models can query it for research context. This is intentional — the content is public-facing knowledge about Bitcoin mining.

3. **Admin wiki is MCP-airgapped** — `/home/agentorange/wiki/admin/` is owned by `agentorange` user with `chmod 700`. The MCP server runs as a different user and cannot read it. The frontier model literally cannot access it through tool calls. You access it via SSH or scripts running as `agentorange`.

4. **Radicle originates from meetup wiki only** — Admin wiki stays local. No Radicle, no website sync.

5. **Mac + Obsidian sync meetup wiki only** — Admin wiki lives on agentorange and nowhere else.

### Source Material Location

Sources from the Mac transfer to both wikis depending on content type:

```
Mac → agentorange staging → split by content type

Public (meetup/wiki):
  ~/Downloads/*.pptx/*.pdf  →  meetup/wiki/raw/presentations/
  ~/Downloads/meetup-demo-*  →  meetup/wiki/raw/transcripts/
  ~/sovereign-digest/*       →  meetup/wiki/raw/code/ (clean versions)
  ~/braiins-ocean-tools/*    →  meetup/wiki/raw/code/

Private (wiki/admin):
  ~/docs/agentorange-evolution-roadmap.md  →  admin/wiki/entities/
  ~/docs/agent-security-roadmap.md        →  admin/wiki/entities/
  ~/scorp-mining-toolkit/BUSINESS_CONTEXT →  admin/wiki/entities/
  (any operational, config, or security content)
```

### Conflict Model

| Actor | Meetup Wiki | Admin Wiki | Conflicts? |
|--|--|--|--|
| Hermes Agent (via MCP) | Read/write via `read_file`/`write_file` | **Cannot read** — Linux perms | No — gated by filesystem |
| You (SSH agentorange) | Read/write | Read/write | No — you control timing |
| MCP`/`frontier models | Can query via MCP tools | **Cannot reach** — blocked at OS level | No — air-gap enforced |
| Contributors (Radicle) | Patches to meetup wiki | N/A | Reviewed before merge |
| Website sync | One-directional pull | N/A | N/A |


---

## Phase 0: Pre-Flight — Source Transfer to agentorange

**0.1** Verify SSH connectivity to agentorange (currently timing out from Mac — may need to resolve network/routing first).

**0.2** On agentorange, create staging directories:
```bash
mkdir -p /agent/staging/meetup-ingest /agent/staging/admin-ingest
```

**0.3** Transfer source files from Mac to agentorange staging (once SSH works):
```bash
# Public sources → meetup staging
scp ~/Downloads/MiningLiketheBigPlayers-v3.pptx \
    ~/Downloads/MiningLiketheBigPlayers-v4.pdf \
    ~/Downloads/rrbtc-mining-hashpower-datum-2026-05-v2.pptx \
    agentorange:/agent/staging/meetup-ingest/
scp ~/Downloads/meetup-demo-cheatsheet.md \
    agentorange:/agent/staging/meetup-ingest/
scp -r ~/sovereign-digest/HASHGUARD_README.md \
    ~/sovereign-digest/hashguard.py \
    ~/sovereign-digest/braiins_api_v1_spec.yml \
    ~/sovereign-digest/mining_report.py \
    ~/sovereign-digest/ocean_payout_alert.py \
    ~/sovereign-digest/profit_report.py \
    agentorange:/agent/staging/meetup-ingest/sovereign-digest/
scp -r ~/braiins-ocean-tools/ \
    agentorange:/agent/staging/meetup-ingest/braiins-ocean-tools/

# Private sources → admin staging
scp -r ~/docs/agentorange-evolution-roadmap.md \
    ~/docs/agent-security-roadmap.md \
    agentorange:/agent/staging/admin-ingest/
scp -r ~/scorp-mining-toolkit/BUSINESS_CONTEXT.md \
    ~/scorp-mining-toolkit/README.md \
    ~/scorp-mining-toolkit/TRACKING_TEMPLATES.md \
    ~/scorp-mining-toolkit/ASSISTANT_INSTRUCTIONS.md \
    agentorange:/agent/staging/admin-ingest/scorp-mining-toolkit/
```

**0.4** Verify transfer completeness (file counts, sizes match expected).

**0.5** If SSH from Mac is blocked, reverse direction: pull from agentorange or use alternative transfer (Python HTTP server on Mac, `transfer.sh`, etc.).


---

## Phase 1: Meetup Wiki Initialization

**1.1** Create directory structure at `/agent/files/meetup/wiki/`:
```
/agent/files/meetup/wiki/
├── SCHEMA.md                    # Domain, conventions, tag taxonomy
├── index.md                     # Sectioned content catalog (1-line summaries)
├── log.md                       # Chronological action log (append-only)
├── raw/                         # Layer 1: Immutable source material
│   ├── presentations/           # Slide decks (PPTX, PDF)
│   ├── articles/                # Web articles, clippings
│   ├── papers/                  # PDFs, technical specs
│   ├── transcripts/             # Meeting notes, demo scripts
│   ├── code/                    # Scripts, configs (read-only refs)
│   └── assets/                  # Images, diagrams
├── entities/                    # Layer 2: People, orgs, products, pools
├── concepts/                    # Layer 2: Topics (hashrate, templates, etc.)
├── comparisons/                 # Layer 2: Side-by-side analyses
├── queries/                     # Layer 2: Filed query results
├── presentations/               # Generated outlines from wiki content
└── _archive/                    # Superseded content
```

**1.2** Write `SCHEMA.md` — domain: Bitcoin mining, hashrate marketplaces, template control, sovereign automation.
- **Tag taxonomy:** mining, pooling, protocol, node-software, marketplace, automation, economy, governance, research
- **Page thresholds:** Create page when entity appears in 2+ sources, max 200 lines before split
- **Wikilinks:** Every page must have ≥2 outbound `[[wikilinks]]`
- **Neutral framing:** Contentious topics (BIP-110, Core vs Knots) must present both sides without declaring a winner

**1.3** Set `WIKI_PATH=/agent/files/meetup/wiki` in agentorange's shell env file for persistent skill reference.


---

## Phase 2: Admin Wiki Initialization (Private, Air-Gapped)

**2.1** Create directory structure at `/home/agentorange/wiki/admin/`:
```bash
mkdir -p /home/agentorange/wiki/admin/
chmod 700 /home/agentorange/wiki/admin/  # Block MCP user
```
```
/home/agentorange/wiki/admin/
├── SCHEMA.md                    # Domain, conventions
├── index.md                     # Content catalog
├── log.md                       # Action log
├── raw/                         # Immutable sources
│   ├── configs/                 # Server configs, system files
│   ├── meeting-notes/           # Internal planning notes
│   └── code/                    # Internal scripts
├── entities/                    # Services, machines, tools
│   ├── ollama.md
│   ├── mcp-server.md
│   ├── trymaple.md
│   ├── hermes-agent.md
│   ├── open-webui.md
│   ├── searxng.md
│   ├── hashrate-autopilot.md
│   ├── signal-bridge.md
│   ├── radicle-node.md
│   └── agentorange-hardware.md
├── concepts/                    # Operational patterns
│   ├── approval-gates.md
│   ├── tiered-routing.md
│   ├── port-architecture.md
│   ├── linux-user-isolation.md
│   └── credential-architecture.md
├── comparisons/                 # Trade-off analyses
│   ├── mcp-auth-strategies.md
│   └── config-approaches.md
├── queries/                     # Filed research
└── _archive/
```

**2.2** Write `SCHEMA.md` — domain: systems operations, server administration, security.
- **Tag taxonomy:** service, hardware, network, security, pipeline, config, troubleshooting
- **Page thresholds:** Same as meetup wiki (2+ sources, 200 lines max)
- **No wikilinks minimum** — content may be standalone (many pages reference things that don't have their own page yet) but linking is encouraged
- **Confidence markers** same as meetup wiki
- **No publish targets** — admin wiki never goes to Radicle or website

**2.3** Initial ingest from staged admin sources:
- `agentorange-evolution-roadmap.md` → parse into `entities/agentorange-hardware.md`, `entities/ollama.md`, `entities/mcp-server.md`
- `agent-security-roadmap.md` → parse into `concepts/credential-architecture.md`, `concepts/linux-user-isolation.md`, `concepts/approval-gates.md`
- `scorp-mining-toolkit/BUSINESS_CONTEXT.md` → `entities/` as business context page

**2.4** Update `index.md`, `log.md`. **Stop for review.** Admin wiki operational before continuing with meetup wiki ingestion.


---

## Phase 3: Ingest Meetup Slides (Meetup Wiki)

**Sources (from Phase 0 staging):**
- `MiningLiketheBigPlayers-v3.pptx` (23 slides)
- `MiningLiketheBigPlayers-v4.pdf` (Canva export)
- `rrbtc-mining-hashpower-datum-2026-05-v2.pptx`
- `meetup-demo-cheatsheet.md` (speaker script)

**3.1** Move presentations to `meetup/wiki/raw/presentations/` with descriptive names and raw frontmatter (`source_url`, `ingested`, `sha256`).

**3.2** Extract text from PPTX files using Python zipfile+XML fallback.

**3.3** Extract text from PDF (try `pdftotext`, fall back to copy-paste).

**3.4** Move `meetup-demo-cheatsheet.md` to `meetup/wiki/raw/transcripts/`.

**3.5** Create initial wiki pages (~12-15 pages):

| File | Type | Source |
|--|--|--|
| `concepts/rented-hashrate-marketplace.md` | concept | Slides 10-11 |
| `concepts/datum-protocol.md` | concept | Slides 9, 15 |
| `concepts/stratum-v2.md` | concept | Slides 15, research refs |
| `concepts/block-template-control.md` | concept | Slides 9, 15 |
| `concepts/solo-vs-pooled-mining.md` | concept | Slide 12 |
| `concepts/pay-your-bid.md` | concept | Slide 11 |
| `concepts/stall-detection.md` | concept | Slide 13 |
| `entities/braiins-hashpower.md` | entity | Slides 10-11, research refs |
| `entities/ocean-xyz.md` | entity | Slides 12, 15, research refs |
| `entities/hashguard.md` | entity | Slides 13, 18 |
| `entities/hashrate-autopilot.md` | entity | Slide 14 |
| `comparisons/core-vs-knots.md` | comparison | Slide 16 |
| `comparisons/hashguard-vs-autopilot.md` | comparison | Slide 14 |

**3.6** Verify: every new page links to ≥2 others. Update `index.md`, `log.md`. **Stop for review.**


---

## Phase 4: Ingest Tooling & Codebase Context (Split by Sensitivity)

**Public items → Meetup Wiki:**

From staged `meetup-ingest/sovereign-digest/`:
- `HASHGUARD_README.md` → `meetup/wiki/raw/code/`
- `hashguard.py` → `meetup/wiki/raw/code/`
- `braiins_api_v1_spec.yml` → `meetup/wiki/raw/code/`
- `mining_report.py`, `ocean_payout_alert.py`, `profit_report.py`, `wallet_manager.py`, `auto_order.py` → `meetup/wiki/raw/code/`

From staged `meetup-ingest/braiins-ocean-tools/`:
- `README.md`, `hashguard.py`, `mining_report.py`, `profit_report.py` → `meetup/wiki/raw/code/`

From agentorange native:
- `/agent/hashrate-autopilot/` — config, readme (not full source) → `meetup/wiki/raw/code/`

Create/update meetup wiki pages:
- `entities/hashguard.md` (add architecture details from README)
- `entities/braiins-hashpower.md` (add API quirks)
- `concepts/sovereign-digest-pipeline.md` (the full tool suite)
- `concepts/radicle-tool-distribution.md`

**Private items → Admin Wiki:**

From staged `admin-ingest/`:
- `scorp-mining-toolkit/BUSINESS_CONTEXT.md`, `README.md`, `TRACKING_TEMPLATES.md`, `ASSISTANT_INSTRUCTIONS.md` → `admin/wiki/raw/code/`

Create/update admin wiki pages:
- `entities/scorp-mining-toolkit.md` — business process, pipeline scripts, data formats
- `entities/private-data-pipeline.md` — CSV formats, field mappings, rulebook
- `concepts/csv-format-reference.md` — field mapping reference for all known sources

**Cross-reference:** Mining concepts in Phase 4 link back to Phase 3 slide pages in the meetup wiki. Admin wiki entities reference each other. Update `index.md`, `log.md` for both wikis. **Stop for review.**


---

## Phase 5: Ingest Website Content (Meetup Wiki)

**5.1** Identify website URLs (need to confirm from you).

**5.2** For each site:
- `web_extract` each page
- Save to `meetup/wiki/raw/articles/` with frontmatter
- Create/update wiki pages

**5.3** Priority external sources (already referenced in slides):
- `https://hashpower.braiins.com/` — live market data
- `https://academy.braiins.com/en/braiins-hashpower/about/` — Braiins docs
- `https://ocean.xyz/datum` — DATUM protocol
- `https://stratumv2.org` — Sv2 spec
- `https://dmnd.work` — Sv2 reference implementation
- `https://bips.dev/110/` — BIP-110 spec
- Community resources (BitAxe, Start9, Radicle onboarding)

**5.4** Flag fast-moving topics (hashprice, market stats) with `confidence: low`. **Stop for review.**

---

## Phase 6: Branching — External Research (Meetup Wiki)

**6.1** Priority research topics:
- Pool centralization data
- BIP-110 community discourse
- Bitcoin mining economics / hashprice trends
- Sovereign node setups
- Lightning mining payouts (Bolt 12)
- Stratum V2 adoption metrics

**6.2** Ongoing ingestion pattern:
- `web_search` per topic
- `web_extract` for full articles/specs
- Create/update pages per schema rules
- Flag contested topics with `contested: true` + neutral framing

**6.3** Quality gates:
- Lint before publicizing
- Verify tags against SCHEMA.md taxonomy
- Cross-reference within meetup wiki


---

## Phase 7: Radicle Publishing (Meetup Wiki Only)

**7.1** Git remotes already configured on agentorange:
```
rad     rad://z3gAUxMoQvVVFYcX1qZPdo8PLAY2Q (fetch)
rad     rad://z3gAUxMoQvVVFYcX1qZPdo8PLAY2Q/z6MkmBj5FPhGtQzxBsxnHHTcZDXPhb2zU2HZixL12gAX4oCv (push)
```

**7.2 IMPORTANT:** The delegate key lives on wakazashi. Pushing `git push rad master` from agentorange updates local git refs but does **not propagate** to the Radicle network. See Appendix B for the full delegate-push workflow using git bundles.

**7.3** Contributor workflow:
```bash
rad clone rad:<repo-id>
# Edit .md files, submit patch
rad patch  # submit changes for review
```

**7.4** Review workflow:
```bash
rad patch list
rad patch show <id>
rad patch checkout <id> && review && rad patch merge <id>
```


---

## Phase 8: Website Publishing (Meetup Wiki Only)

**8.1** Determine website server (need to confirm from you).

**8.2** Publish public subset:
```bash
# Exclude raw/, queries/, _archive/
rsync -avz --exclude='.git' --exclude='.radicle' \
  --exclude='raw/' --exclude='queries/' --exclude='_archive/' \
  /agent/files/meetup/wiki/ user@webserver:/var/www/wiki/
```

**8.3** What the public sees:
- `entities/*.md`, `concepts/*.md`, `comparisons/*.md`, `presentations/*.md`, `index.md`

---

## Phase 9: Mac + Obsidian Sync (Meetup Wiki Only)

**9.1** Pull meetup wiki to Mac:
```bash
rsync -avz --exclude='.git' --exclude='.radicle' \
  agentorange:/agent/files/meetup/wiki/ ~/meetup-wiki/
```

**9.2** Open `~/meetup-wiki/` as Obsidian vault. Read-only — edits go to canonical source on agentorange.

**9.3** Admin wiki does not sync to Mac. If you need to reference it from the Mac, SSH in and read it directly.

---

## Phase 10: Ongoing Maintenance

**10.1** Ingest new slides/research as created.

**10.2** Lint after every major ingest (both wikis).

**10.3** Source drift monitoring via sha256 on re-ingest.

**10.4** Log rotation at 500 entries.

**10.5** Archive policy: superseded content → `_archive/`.

**10.6** Radicle patch review periodically.

**10.7** Admin wiki grows organically — document as you discover things.


---

## Step 10: 3060 Embedding + Vector Search (Infrastructure)

After the meetup wiki has content, add the embedding layer:

```bash
ollama pull nomic-embed-text
# Run Chroma in Docker, index /agent/files/meetup/wiki/entities/ and /concepts/
# 3060: 0.5GB VRAM for embeddings, near-zero impact on chat model
```

See the orchestration tasks list for full breakdown — this is the top-priority addition after wiki content exists.

---

## Stop Points & Verification

Each phase ends with a **stop point**. Before proceeding:
1. Verify `index.md` complete for both wikis
2. Run lint: orphan pages, broken wikilinks, missing frontmatter, tag compliance
3. Confirm page quality (scannable, cross-referenced, tagged correctly)
4. You review and approve before next phase

---

## Dependencies & Open Questions

- **SSH to agentorange** — Timing out from Mac. Must resolve before Phase 0 transfers.
- **Radicle on agentorange** — rad CLI missing. Delegate key on wakazashi.
- **Meetup website URL** — Needed for Phase 5 and Phase 8.
- **Website server identity** — Is it agentorange itself or a separate machine?
- **PDF extraction** — Canva-encoded PDFs may need manual copy-paste.
- **Large ingests** — Will confirm scope before executing.
- **Meetup wiki initial scope** — Phase 1-6 build the foundation; Step 10 (embeddings) is post-content.


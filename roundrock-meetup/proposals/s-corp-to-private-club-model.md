# S-Corp to Private Club Membership Model Proposal

## Overview
This proposal outlines transitioning the Round Rock Bitcoiners from an S-Corporation structure to a private club membership model using Radicle for transparent record-keeping and evolving governance, with Bitcoin multisig as the binding treasury mechanism.

## Problem Statement
The current S-Corp structure creates unnecessary complexity, tax overhead, and centralization barriers for a community-driven Bitcoin meetup group. Key issues include:
- Annual tax filing requirements and associated costs
- Centralized control contradicting Bitcoin's decentralization ethos
- Administrative burden distracting from community building
- Difficulty in aligning incentives with community values
- Need for transparent, auditable treasury management without corporate overhead

## Proposed Solution
Transition to a private club membership model using:
- **Radicle/Git** for transparent, auditable record-keeping of proposals and decisions
- **Bitcoin treasury** managed via multisig wallets (e.g., Sparrow, Nunchuk) - the binding governance mechanism for all spending
- **Membership model** where contributions grant influence over treasury allocations (proposed example: 0.001 BTC [~$75] per quarter)
- **Simple communication tools** (Telegram, Signal, Keet, SimpleX) for discussion and informal consensus-building
- **Retention and open-sourcing of current assets** (hashguard.py, meetup infrastructure) under the RoundRock-Meetup Radicle repository

## Benefits
- **Tax Efficiency**: At current operating scale, a Texas unincorporated association under Ch. 252 has no state or federal filing requirement provided the treasury operates at cost with no net income
- **Decentralization**: No single point of control; treasury decisions require multisig consensus
- **Administrative Simplicity**: Reduced overhead compared to corporate structure
- **Member Alignment (Skin in the Game)**: Contributing members have direct incentive to make sound treasury decisions because their own sats are in the pool
- **Pseudonymity Support**: Members can participate in Bitcoin/Radicle layers pseudonymously. Multisig signers may use pseudonymous keys, but must be socially known and trusted by the group.
- **Community Focus**: Resources directed toward meetup activities rather than corporate compliance
- **Transparent Records**: All treasury actions and decisions archived in Git for member review

## Membership Structure

### Roles
1. **Signers** - Multisig keyholders (3-of-5) and operational stewards. Signers rotate periodically. New signers added by consensus of existing signers, documented in Git.
2. **Contributors** - Members with documented participation in treasury or labor, tracked in Git. Contributors have voice in treasury decisions and may become signers over time.
3. **Participants** - Anyone who shows up. No dues or tracking required; can propose topics and participate in discussion but do not hold binding voting rights on treasury spends.

### Contributions & Benefits
- **Contribution**: Bitcoin (sats) via multisig treasury
- **Voting Rights**: Only Signers and Contributors who are current on dues may vote on treasury allocations and proposals
- **Benefits**: 
  - Priority access to present topics
  - Potential group buy discounts and member perks such as access to hardware, workshops, swag, etc. (treasury-dependent)
  - Reputation within the community
  - Ability to propose and lead initiatives
  - Influence over discretionary spending as treasury grows through membership expansion

## Governance Model

| Layer | Tool | Purpose | Binding? |
|-------|------|---------|----------|
| 1 | Telegram / Signal / chat | Discussion & brainstorming | **Never** |
| 2 | Polls / meetup votes | Sentiment & consensus-building | **Never** |
| 3 | Multisig transaction | Spending & treasury execution | **Always** |

### Layer 1: Communication & Discussion (Multi-Platform)
- **Purpose**: Informal discussion, brainstorming, social coordination
- **Tools**:
  - **Telegram** - general chat, announcements (where most members already are)
  - **Signal** - smaller group for privacy-sensitive coordination (native polling available)
  - **Keet / SimpleX** - direct/1:1 comms for members who prefer maximum privacy (no group polling)
- **Binding status**: **NEVER** - chat is communication only, never governance
- **Pseudonymity note**: Members who prefer privacy can participate in Bitcoin/Radicle layers pseudonymously while using any chat platform for social coordination

### Layer 2: Proposal & Consensus (Meetups + Polls)
- **Purpose**: Gauge sentiment, build consensus, document proposals
- **Tools**:
  - **Telegram polls** - general interest/sentiment (easy, everyone can participate)
  - **Signal polls** - more sensitive decisions among the Signal group
  - **Show-of-hands at meetups** - in-person consensus building
- **Binding status**: **NEVER** - polls and votes at this layer are sentiment-only. They inform Layer 3 decisions but do not authorize spending.
- **Documentation**: Proposals and discussion summaries archived to Git/Radicle for transparency

### Layer 3: Binding Treasury Decisions (Multisig)
- **The actual vote**: Any treasury spend requires 3-of-5 multisig signatures
- **Signer pool**: Initial signers are founding members. Signer composition may evolve as contributors demonstrate sustained participation.
- **Signer identity**: Signers may use pseudonymous keys, but must be socially known and trusted by the group. Cryptographic verification (signed messages, xpub verification) supplements but does not replace social trust.
- **Process**: 
  1. Proposal discussed in Layer 1-2
  2. If consensus emerges, a signer creates the multisig transaction
  3. 2 additional signers review and sign
  4. Transaction executes on-chain (immutable, auditable, timestamped)
- **Dispute resolution**: If consensus cannot be reached, no spend occurs (default = status quo)
- **This is the only binding governance mechanism** - everything else is communication

### Treasury Management
- **Multisig Wallet**: 3-of-5 setup. Initial signers are founding members. Signer composition may evolve as contributing members demonstrate sustained participation - new signers added by consensus of existing signers, documented in Git.
- **Funding Sources**: Member contributions, sponsorships, donation drives
- **Monthly Operating Expenses**: ~$200-$400
  - Venue rental: ~$75
  - Pizza and drinks: ~$125
  - Hosting, meetup.com fees, misc.: ~$200
- **Allocations**: 
  - Venue costs and refreshments (primary expense)
  - Small tokens of appreciation: hats, t-shirts, swag for speakers and active contributors
  - Speaker honorariums - future aspiration only, not budgeted at current scale
  - Equipment for group activities (mining hardware, nodes, etc.) - treasury-dependent
  - Educational materials and resources
  - Emergency reserve: target 6 months of operating expenses (~$1,200-$2,400)
- **Transparency**: All transactions viewable on-chain; rationale documented in Git

## Implementation Roadmap

### Phase 1: Foundation (Month 1)
- Finalize multisig wallet setup with founding members
- Transfer non-monetary assets to community ownership (website, domains, logos, service subscriptions, open source code repositories). Any existing monetary holdings (including Bitcoin) will be liquidated rather than transferred.
- Document fair market value of all liquidated assets on liquidation date for the final S-Corp tax return
- Open-source hashguard.py under the RoundRock-Meetup Radicle repository
- Establish contribution mechanism and membership tracking
- Host inaugural membership drive meeting

### Phase 2: Operations (Months 2-3)
- Begin regular contribution collection
- Formalize proposal process (Telegram/Signal/meetup discussion, then Git documentation, then multisig execution)
- Host first member-proposed topic
- Establish regular meeting cadence with membership benefits

### Phase 3: Growth (Months 4-6)
- Establish contributor reputation tracking in Git by pseudonym/Bitcoin address
- Explore educational initiatives and workshops
- Establish partnerships with other Bitcoin communities

## Legal & Tax Considerations
- Operate as Texas unincorporated association under [Tex. Bus. Orgs. Code § 252](https://texas.public.law/statutes/tex._bus._orgs._code_title_6_chapter_252)
- Membership dues to operate-at-cost associations are generally not taxable income to the organization
- Members are individually responsible for capital gains obligations when contributing appreciated BTC - disposing of BTC is a personal taxable event regardless of club structure
- Maintain clear separation between personal and community Bitcoin holdings
- **Wind-down of existing S-Corp**: File dissolution with Texas Secretary of State, submit final tax return, close business accounts (strongly recommended to consult a TX business attorney specializing in non-profit/crypto entities for this process)
- **Transparent records for member review and potential audits**:
  - Git/Radicle commit history documenting all proposals and decisions
  - On-chain multisig transaction records (immutable, timestamped)
  - Archived meeting notes and discussion summaries

## Resources & References

### Legal & Regulatory
- [Texas Uniform Unincorporated Nonprofit Association Act (Tex. Bus. Orgs. Code Ch. 252)](https://texas.public.law/statutes/tex._bus._orgs._code_title_6_chapter_252)
- [CLARITY Act (H.R. 3633)](https://www.congress.gov/bill/119th-congress/house-bill/3633/text) - Not yet passed; offers no current legal protection but signals favorable regulatory direction.

### Risks & Context
- [Samourai Wallet Sentencing - DOJ Press Release](https://www.justice.gov/usao-sdny/pr/founders-samourai-wallet-cryptocurrency-mixing-service-sentenced-five-and-four-years) - Cautionary reference regarding custody and money transmission risk. The club must avoid activities that could be construed as money transmission or custodial services.

### Community Models & Inspiration
- [Bisq DAO](https://bisq.network/dao/) - decentralized governance and compensation model
- [Bitcoin Beach Whitepaper (BUBBLE Framework)](https://www.bitcoinbeach.com/en/whitepaper) - Bitcoin circular economies and trust-first community building
- [Bitcoin Beach Fellowship](https://www.bitcoinbeach.com/blog/bitcoin-beach-fellowship) - knowledge sharing model for Bitcoin community leaders

### Bounty & FOSS Models
- [Stacker News OSCARS - GitHub Repo + Awards Table](https://github.com/stackernews/stacker.news) - fixed-sats-per-difficulty bounty model
- [Stacker News Bounty Discussion](https://stacker.news/items/576004) - bounty mechanics, sybil resistance, dispute handling

### Tools & Guides
- [Radicle documentation](https://docs.radicle.xyz/)
- [Round Rock Meetup Wiki on Radicle](https://app.radicle.xyz/nodes/iris.radicle.xyz/rad:z2e2VbZGT1S72pQiee5aHYL9zktUY) - public knowledge base for the meetup
- [Round Rock Meetup Repo on Radicle](https://radicle.network/nodes/iris.radicle.network/rad%3Az3gAUxMoQvVVFYcX1qZPdo8PLAY2Q/tree/README.md) - main meetup repository
- [Radicle Private Repo Onboarding Guide](https://hackmd.io/2TWrbU_sRmCvkexVUzAUYA) - Watson's guide for Radicle setup
- [Decentralized Project Ideas](https://hackmd.io/@wvwatson/ryWuxygDWx) - Watson's brainstorm doc for Bitcoin/Nostr/Radicle projects
- [Sparrow Wallet](https://sparrowwallet.com/) - recommended PSBT multisig wallet

### Sovereign Engineering Principles
- Bitcoin and open source community practices
- Existing meetup infrastructure: hashguard.py, meetup automation scripts

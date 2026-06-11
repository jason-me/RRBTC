# HashGuard — Braiins Hashpower Auto-Optimizer

Hourly cron daemon that babysits your [Braiins Hashpower](https://hashpower.braiins.com/) bids so you don't wake up to zero hashrate.

## What it does

- **Stall detection** — if a bid's hashrate drops to 0 TH/s, automatically overbids the lowest matching ask by 1 tick (1,000 sats) to restore flow
- **Trim-down** — if delivering but overbidding by >4%, trims back to optimal price to save sats
- **Auto-topup** — pre-places a new bid when any active order drops below 20% remaining balance
- **Profitability ceiling** — never bids above hash value + 10% (calculated from live difficulty)
- **Signal alerts** — sends a notification on every action (stall boost, trim, topup)
- **State logging** — tracks actions and daily price lows for trend analysis

## Setup

### 1. Install dependencies

```bash
# No external packages required — stdlib only (Python 3.8+)
python3 --version
```

### 2. Configure credentials

**Option A — Bitwarden (recommended):**
```bash
# Store your Braiins API token in Bitwarden
bw login
bw unlock
# Create an item named "Braiins Hashpower API" with your token as the password
```

**Option B — Environment variable:**
```bash
export BRAIINS_TOKEN="your_token_here"
```

**Option C — sops/age (for advanced users):**
```bash
# Encrypt your secrets file with age
sops -e --age <your-age-pubkey> secrets.yaml > secrets.enc.yaml
# Decrypt at runtime
eval $(sops -d secrets.enc.yaml)
```

### 3. Configure your pool endpoint

Copy the example run script and fill in your values:
```bash
cp run_hashguard.sh.example run_hashguard.sh
chmod +x run_hashguard.sh
# Edit run_hashguard.sh — add your pool URL and Bitcoin address
```

**Never commit `run_hashguard.sh`** — it contains your payout address. It's in `.gitignore`.

### 4. Run manually to test

```bash
./run_hashguard.sh
# or
python3 hashguard.py
```

### 5. Schedule with cron (hourly)

```bash
crontab -e
# Add:
0 * * * * /path/to/sovereign-digest/run_hashguard.sh
```

**macOS LaunchAgent** — see `launchd` docs or use the provided plist example.

## Configuration

Edit the `# --- Config ---` section in `hashguard.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `TICK_SIZE` | 1000 | Minimum price increment (sats) |
| `MAX_OVERBID_PCT` | 0.10 | Max overbid above hash value (10%) |
| `TOPUP_THRESHOLD_PCT` | 20 | Pre-topup when order is 80% spent |
| `TOPUP_SPEED_PH` | 1 | PH/s for auto-topup orders |
| `TOPUP_RESERVE` | 10000 | Sats to keep in reserve |

## API notes

- Uses Braiins `/v1/` API (not `/api/v1/` — the OpenAPI spec has a typo)
- Hash value is calculated from difficulty via `/webapi/difficulty-stats` since the v1 API doesn't expose it directly
- Braiins uses **pay-your-bid** pricing — your bid price is what you pay, not the clearing ask price

## License

MIT

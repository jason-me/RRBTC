#!/usr/bin/env python3
"""
HashGuard — Braiins Hashpower auto-optimizer
Runs hourly. If hash delivery stalls (TH/s == 0), automatically overbids
the lowest matching price by 1 tick (1000 sats) to restore flow.
Also logs state for trend analysis.

Strategy:
- If delivering: do nothing (stay cheap)
- If overbidding by >4%: trim back to optimal
- If stalled: overbid lowest matching + 1 tick
- Never bid above hash value (would be unprofitable)
- Report actions via Signal

API Notes (2026-04-15):
- Uses official /v1/ API (NOT /api/v1/ as incorrectly stated in OpenAPI spec)
- OpenAPI spec at /api/openapi.yml says server is /api/v1 but actual API is at /v1/
- Field names match spec: hr_matched_ph, speed_limit_ph, hr_available_ph
- Response format: {"items": [...]} for bid lists
- Hash value calculated from difficulty (no endpoint provides it directly)

Credential setup (choose one):
  Option A — Bitwarden CLI:
    Store your Braiins API token in Bitwarden as "Braiins Hashpower API"
    bw unlock && bw sync

  Option B — Environment variable:
    export BRAIINS_TOKEN=<your token>

  Option C — sops/age encrypted file:
    sops -d secrets.enc.yaml | source /dev/stdin
"""

import json
import os
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

# --- Secrets ---

def get_bw_secret(item_name: str, field: str = "password") -> str:
    """Fetch a secret from Bitwarden CLI. Caches result for session."""
    cache_key = f"_bw_{item_name}_{field}"
    if cache_key in globals():
        return globals()[cache_key]
    try:
        env = {**os.environ, "NODE_TLS_REJECT_UNAUTHORIZED": "0"}
        result = subprocess.run(
            ["bw", "get", field, item_name],
            capture_output=True, text=True, timeout=30, env=env
        )
        if result.returncode == 0:
            globals()[cache_key] = result.stdout.strip()
            return globals()[cache_key]
        print(f"[hashguard] bw get {field} {item_name} failed: {result.stderr[:100]}")
    except Exception as e:
        print(f"[hashguard] Bitwarden fetch error: {e}")
    return ""

def get_braiins_token():
    """Get Braiins API token — env var takes priority, then Bitwarden."""
    global BRAIINS_TOKEN
    if BRAIINS_TOKEN:
        return BRAIINS_TOKEN
    BRAIINS_TOKEN = os.getenv("BRAIINS_TOKEN") or get_bw_secret("Braiins Hashpower API")
    return BRAIINS_TOKEN

# --- Config ---
# Customize these for your setup. No secrets belong here.

BRAIINS_TOKEN = None  # Lazy-loaded — see get_braiins_token() above

BRAIINS_API     = "https://hashpower.braiins.com/v1"
TICK_SIZE       = 1000  # sats — minimum price increment on the Braiins orderbook
MAX_OVERBID_PCT = 0.10  # 10% — max we'll bid above hash value (uptime > profitability)
TOPUP_THRESHOLD_PCT = 20  # % remaining — pre-place new bid when order drops below this
TOPUP_SPEED_PH  = 1       # PH/s — target hashrate for auto-topup orders
TOPUP_RESERVE   = 10000   # sats — always keep this much in reserve

# Your pool/DATUM endpoint — replace with your own stratum URL and payout address
# Examples:
#   Ocean + DATUM:  stratum+tcp://<your-datum-host>:23334
#   Public Pool:    stratum+tcp://pool.public-pool.io:21496
#   Braiins Pool:   stratum+tcp://stratum.braiins.com:3333
POOL_URL      = os.getenv("POOL_URL", "stratum+tcp://YOUR_POOL_HOST:PORT")
POOL_IDENTITY = os.getenv("POOL_IDENTITY", "YOUR_BTC_ADDRESS.HashGuard")

# Signal notifications (optional — remove signal_send() calls if not using Signal)
# Requires signal-cli running locally: https://github.com/AsamK/signal-cli
SIGNAL_RPC_URL   = os.getenv("SIGNAL_RPC_URL", "http://127.0.0.1:8080/api/v1/rpc")
SIGNAL_ACCOUNT   = os.getenv("SIGNAL_ACCOUNT", "")   # Your Signal phone number e.g. +15551234567
SIGNAL_RECIPIENT = os.getenv("SIGNAL_RECIPIENT", "")  # Recipient: phone number or username

# State file — tracks actions and daily price lows
STATE_FILE = Path(os.getenv("HASHGUARD_STATE_DIR", Path.home() / "hashguard" / "state")) / "hashguard_state.json"

# --- Helpers ---

def fetch(url, method="GET", data=None, headers=None):
    h = {
        "User-Agent": "HashGuard/1.0",
        "Content-Type": "application/json",
        "apikey": get_braiins_token(),
    }
    if headers:
        h.update(headers)
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": f"HTTP {e.code}: {body[:200]}"}
    except Exception as e:
        return {"error": str(e)}

def signal_send(message):
    """Send a Signal message. Silently skips if SIGNAL_ACCOUNT not configured."""
    if not SIGNAL_ACCOUNT or not SIGNAL_RECIPIENT:
        return False
    if SIGNAL_RECIPIENT.startswith("+"):
        recipient_param = {"recipient": [SIGNAL_RECIPIENT]}
    else:
        recipient_param = {"username": SIGNAL_RECIPIENT}
    payload = {
        "jsonrpc": "2.0",
        "method": "send",
        "params": {"account": SIGNAL_ACCOUNT, "message": message, **recipient_param},
        "id": f"hg_{int(time.time())}",
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(SIGNAL_RPC_URL, data=data,
                                  headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return "error" not in json.loads(resp.read())
    except:
        return False

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"actions": [], "last_run": None}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

# --- Core logic ---

def get_active_bids():
    d = fetch(f"{BRAIINS_API}/spot/bid/current")
    return d.get("items", []) if "error" not in d else []

def get_orderbook():
    return fetch(f"{BRAIINS_API}/spot/orderbook")

def get_hash_value():
    """
    Calculate hash value = expected mining earnings per EH/day in sats.
    Formula: (block_subsidy * blocks_per_day * 1e8) / (difficulty * 2^32 / 1e18)
    This is what the Braiins UI calculates client-side for the "hash value" line.

    Note: /v1 API doesn't have a difficulty endpoint, so we use /webapi/difficulty-stats
    """
    diff_data = fetch("https://hashpower.braiins.com/webapi/difficulty-stats")
    if "error" in diff_data:
        return None
    difficulty = diff_data.get("difficulty")
    if not difficulty:
        return None
    block_subsidy = 3.125  # BTC per block (post-2024 halving)
    blocks_per_day = 144
    expected_blocks = (1e18 * 86400) / (difficulty * (2**32))
    btc_per_eh_day = expected_blocks * block_subsidy
    return int(btc_per_eh_day * 1e8)

def move_bid(bid_id, new_price_sat):
    """Update bid price via Braiins API."""
    return fetch(f"{BRAIINS_API}/spot/bid", method="PUT", data={
        "bid_id": bid_id,
        "new_price_sat": new_price_sat,
        "memo": "HashGuard auto-adjust"
    })

def get_balance():
    """Return available balance in sats."""
    d = fetch(f"{BRAIINS_API}/account/balance")
    if "error" not in d and "accounts" in d:
        return d["accounts"][0].get("available_balance_sat", 0)
    return 0

def get_lowest_available_ask(ob):
    """Find the cheapest ask with available (unmatched) supply."""
    asks = ob.get("asks", [])
    available = [a for a in asks if a.get("hr_available_ph", 0) > a.get("hr_matched_ph", 0)]
    if not available:
        return None
    cheapest = min(available, key=lambda a: a.get("price_sat", 0))
    return int(cheapest.get("price_sat", 0))

def update_daily_low(state, price_sat):
    """Track the lowest ask price seen today. Resets at midnight UTC."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("daily_low_date") != today:
        state["daily_low_date"] = today
        state["daily_low_sat"] = price_sat
    elif price_sat and price_sat < state.get("daily_low_sat", 999999999):
        state["daily_low_sat"] = price_sat
    return state.get("daily_low_sat")

def place_bid(price_sat, amount_sat, worker_suffix="AutoTopup"):
    """Place a new bid via Braiins API."""
    return fetch(f"{BRAIINS_API}/spot/bid", method="POST", data={
        "price_sat": price_sat,
        "amount_sat": amount_sat,
        "speed_limit_ph": TOPUP_SPEED_PH,
        "dest_upstream": {
            "url": POOL_URL,
            "identity": f"{POOL_IDENTITY.rsplit('.', 1)[0]}.{worker_suffix}"
        },
        "memo": "HashGuard auto topup"
    })

def topup_needed(bids):
    """Return True if any active bid is below threshold and not exhausted."""
    for b in bids:
        est = b.get("state_estimate", {})
        progress = est.get("progress_pct", 0)
        remaining = est.get("amount_remaining_sat", 0)
        if remaining > 0 and progress >= (100 - TOPUP_THRESHOLD_PCT):
            return True
    return False

def already_topping_up(bids):
    """Check if a HashGuard auto-topup bid is already active."""
    for b in bids:
        bid = b.get("bid", {})
        memo = bid.get("memo", "")
        if "auto topup" in memo.lower() or "hashguard" in memo.lower():
            return True
    return False

def run():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    state = load_state()
    state["last_run"] = now
    actions = []
    log = [f"[HashGuard] {now}"]

    if not get_braiins_token():
        log.append("ERROR: BRAIINS_TOKEN not set — set BRAIINS_TOKEN env var or store in Bitwarden as 'Braiins Hashpower API'")
        save_state(state)
        print("\n".join(log))
        return

    bids = get_active_bids()
    if not bids:
        log.append("No active orders — nothing to do")
        save_state(state)
        print("\n".join(log))
        return

    ob = get_orderbook()
    if "error" in ob:
        log.append(f"Orderbook fetch failed: {ob['error']}")
        save_state(state)
        print("\n".join(log))
        return

    ob_bids = ob.get("bids", [])
    matching_bids = [b for b in ob_bids if b.get("hr_matched_ph", 0) > 0]
    lowest_matching_sat = None
    if matching_bids:
        lowest = min(matching_bids, key=lambda b: b.get("price_sat", 0))
        lowest_matching_sat = int(lowest.get("price_sat", 0))

    hash_value_sat = get_hash_value()

    log.append(f"Active orders: {len(bids)}")
    if lowest_matching_sat:
        log.append(f"Lowest matching bid: {lowest_matching_sat:,} sats/EH")
    if hash_value_sat:
        log.append(f"Hash value: {hash_value_sat:,} sats/EH")

    total_speed = sum(b.get("state_estimate", {}).get("avg_speed_ph", 0) * 1000 for b in bids)
    log.append(f"Total TH/s: {total_speed:.0f}")

    for b in bids:
        bid = b.get("bid", {})
        est = b.get("state_estimate", {})
        bid_id = bid.get("id")
        dest = bid.get("dest_upstream", {}).get("identity", "")
        worker = dest.split(".")[-1] if "." in dest else dest
        speed_ths = est.get("avg_speed_ph", 0) * 1000
        current_price = bid.get("price_sat", 0)
        remaining = est.get("amount_remaining_sat", 0)

        if remaining <= 0:
            log.append(f"  {worker}: exhausted, skipping")
            continue

        # Anchor orders stay at fixed price — mark them and skip
        if "anchor" in worker.lower():
            log.append(f"  {worker}: ANCHOR (protected, skipping)")
            continue

        if speed_ths > 50:  # delivering (>50 TH/s threshold filters noise)
            if lowest_matching_sat:
                optimal_price = lowest_matching_sat + TICK_SIZE
                trim_threshold = int(optimal_price * 1.04)  # only trim if >4% above optimal
                overpay_pct = (current_price - optimal_price) / optimal_price * 100
                if current_price > trim_threshold:
                    log.append(f"  {worker}: delivering {speed_ths:.0f} TH/s @ {current_price//1000:,}k — {overpay_pct:.1f}% over optimal, trimming to {optimal_price//1000:,}k")
                    result = move_bid(bid_id, optimal_price)
                    if "error" not in result:
                        actions.append({"time": now, "worker": worker, "from": current_price, "to": optimal_price, "reason": "trim_down"})
                        log.append(f"  {worker}: trimmed down ✓")
                    else:
                        log.append(f"  {worker}: trim failed — {result.get('error','')[:80]}")
                else:
                    log.append(f"  {worker}: delivering {speed_ths:.0f} TH/s @ {current_price//1000:,}k — {overpay_pct:.1f}% over optimal (within 4% tolerance)")
            else:
                log.append(f"  {worker}: delivering {speed_ths:.0f} TH/s @ {current_price//1000:,}k — OK")
            continue

        # Stalled — overbid lowest matching by 1 tick to restore flow
        log.append(f"  {worker}: STALLED ({speed_ths:.0f} TH/s) @ {current_price//1000:,}k sats")

        if not lowest_matching_sat:
            log.append(f"  {worker}: no matching bids in orderbook, can't overbid")
            continue

        target_price = lowest_matching_sat + TICK_SIZE

        ceiling = int(hash_value_sat * (1 + MAX_OVERBID_PCT)) if hash_value_sat else None
        if ceiling and target_price > ceiling:
            log.append(f"  {worker}: target {target_price:,} exceeds ceiling {ceiling:,} (hash value +10%) — skipping")
            continue

        if target_price <= current_price:
            log.append(f"  {worker}: already at or above target price — no move needed")
            continue

        target_price = round(target_price / TICK_SIZE) * TICK_SIZE

        log.append(f"  {worker}: moving bid {current_price:,} → {target_price:,} sats/EH")
        result = move_bid(bid_id, target_price)

        if "error" not in result:
            actions.append({"time": now, "worker": worker, "from": current_price, "to": target_price, "reason": "stalled"})
            log.append(f"  {worker}: bid moved successfully ✓")
        else:
            log.append(f"  {worker}: move failed — {result.get('error','')[:100]}")

    # Topup logic
    lowest_available_ask = get_lowest_available_ask(ob)
    daily_low = update_daily_low(state, lowest_available_ask)
    if lowest_available_ask:
        log.append(f"Lowest available ask: {lowest_available_ask:,} sats/EH | Daily low: {daily_low:,} sats/EH")

    if topup_needed(bids) and not already_topping_up(bids):
        balance = get_balance()
        spendable = balance - TOPUP_RESERVE

        if spendable < 10000:
            log.append(f"Topup needed but insufficient balance ({balance:,} sats available, {TOPUP_RESERVE:,} reserved)")
        else:
            topup_price = min(
                lowest_available_ask or 999999999,
                daily_low or 999999999
            )
            if topup_price == daily_low and lowest_available_ask and lowest_available_ask > daily_low:
                topup_price = lowest_available_ask
                log.append(f"Daily low {daily_low:,} unavailable, using current best ask {lowest_available_ask:,}")

            ceiling = int(hash_value_sat * (1 + MAX_OVERBID_PCT)) if hash_value_sat else None
            if ceiling and topup_price > ceiling:
                topup_price = ceiling
                log.append(f"Topup price capped at ceiling: {topup_price:,} (hash value +10%)")

            cost_per_day = (topup_price / 1000) * TOPUP_SPEED_PH
            runtime_days = spendable / cost_per_day if cost_per_day > 0 else 0

            log.append(f"Topup: placing {TOPUP_SPEED_PH} PH/s @ {topup_price:,} sats/EH")
            log.append(f"  Budget: {spendable:,} sats → ~{runtime_days:.1f} days runtime")

            worker_id = f"HG{int(time.time()) % 10000}"
            result = place_bid(topup_price, spendable, worker_suffix=worker_id)

            if "error" not in result:
                actions.append({"time": now, "worker": worker_id, "price": topup_price, "amount": spendable, "reason": "topup", "runtime_days": round(runtime_days, 1)})
                log.append(f"  Topup placed successfully ✓ (worker: {worker_id})")
            else:
                log.append(f"  Topup failed: {result.get('error','')[:100]}")
    elif topup_needed(bids) and already_topping_up(bids):
        log.append("Topup needed but HashGuard bid already active — skipping")

    # Signal notification — only fires if we took action
    if actions:
        msg = f"⚡ HashGuard [{now}]\n"
        for a in actions:
            if a.get("reason") == "topup":
                msg += f"🆕 Topup {TOPUP_SPEED_PH} PH/s @ {a['price']//1000:,}k sats/EH | ~{a.get('runtime_days',0)} days\n"
            elif a.get("reason") == "trim_down":
                msg += f"⬇️ Trimmed {a['worker']}: {a['from']//1000:,}k → {a['to']//1000:,}k sats/EH\n"
            else:
                msg += f"⬆️ Boosted {a['worker']}: {a['from']//1000:,}k → {a['to']//1000:,}k sats/EH\n"
        msg += f"TH/s: {total_speed:.0f}"
        signal_send(msg)
        log.append("Signal notification sent")

    state["actions"].extend(actions)
    state["actions"] = state["actions"][-100:]  # keep last 100
    save_state(state)

    print("\n".join(log))

if __name__ == "__main__":
    run()

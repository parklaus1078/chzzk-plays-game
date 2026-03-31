#!/usr/bin/env python3
"""Standalone health check script with Discord webhook alerts.

Usage:
    python scripts/health_check.py [--url http://localhost:8000]

Environment variables:
    DISCORD_WEBHOOK_URL - Optional Discord webhook for alerts
    HEALTH_CHECK_URL - Health endpoint URL (default: http://localhost:8000/api/health)

Exit codes:
    0 - All health checks passed
    1 - One or more health checks failed
"""

import asyncio
import os
import sys
from argparse import ArgumentParser
from datetime import datetime

import httpx


async def send_discord_alert(webhook_url: str, message: str, severity: str = "warning") -> None:
    """Send alert to Discord webhook.

    Args:
        webhook_url: Discord webhook URL
        message: Alert message
        severity: Alert severity (info/warning/error)
    """
    # Discord color codes
    colors = {
        "info": 0x3498DB,      # Blue
        "warning": 0xF39C12,   # Orange
        "error": 0xE74C3C,     # Red
    }

    embed = {
        "title": f"🚨 Health Check Alert - {severity.upper()}",
        "description": message,
        "color": colors.get(severity, 0x95A5A6),
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {
            "text": "Chzzk Plays Gamedev Health Monitor"
        }
    }

    payload = {
        "embeds": [embed]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload, timeout=10.0)
            response.raise_for_status()
    except Exception as exc:
        print(f"Failed to send Discord alert: {exc}", file=sys.stderr)


async def check_health(base_url: str, discord_webhook_url: str | None = None) -> int:
    """Perform health check and send alerts if needed.

    Args:
        base_url: Base server URL
        discord_webhook_url: Optional Discord webhook URL for alerts

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    health_url = f"{base_url}/api/health"
    exit_code = 0
    alerts = []

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(health_url, timeout=10.0)
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPError as exc:
        error_msg = f"❌ Server unreachable: {exc}"
        print(error_msg, file=sys.stderr)
        alerts.append((error_msg, "error"))
        return 1

    except Exception as exc:
        error_msg = f"❌ Health check failed: {exc}"
        print(error_msg, file=sys.stderr)
        alerts.append((error_msg, "error"))
        return 1

    # Print health status
    print("Health Check Results:")
    print(f"  Server OK: {'✓' if data.get('server_ok') else '✗'}")
    print(f"  Database OK: {'✓' if data.get('db_ok') else '✗'}")
    print(f"  Donation Listener: {'✓' if data.get('donation_listener_connected') else '✗'}")
    print(f"  Queue Size: {data.get('queue_size', 'N/A')}")
    print(f"  Current Prompt: {data.get('current_prompt_id', 'None')}")
    print(f"  Daily Cost: ${data.get('daily_cost_usd', 0):.2f}")
    print(f"  Budget Remaining: ${data.get('budget_remaining_usd', 0):.2f}")
    print(f"  Queue Stalled: {'⚠️ YES' if data.get('queue_stalled') else '✓ No'}")

    # Check for issues and generate alerts
    if not data.get("server_ok"):
        alerts.append(("Server health check failed", "error"))
        exit_code = 1

    if not data.get("db_ok"):
        alerts.append(("Database connectivity check failed", "error"))
        exit_code = 1

    if not data.get("donation_listener_connected"):
        alerts.append(("⚠️ Donation listener disconnected", "warning"))
        exit_code = 1

    # Check budget threshold (80% or more)
    daily_cost = data.get("daily_cost_usd", 0)
    budget_remaining = data.get("budget_remaining_usd", 0)
    total_budget = daily_cost + budget_remaining

    if total_budget > 0:
        budget_used_pct = (daily_cost / total_budget) * 100
        if budget_used_pct >= 80:
            msg = f"⚠️ Budget threshold exceeded: {budget_used_pct:.1f}% used (${daily_cost:.2f} / ${total_budget:.2f})"
            alerts.append((msg, "warning"))
            print(f"\n{msg}")

    # Check queue stall
    if data.get("queue_stalled"):
        msg = f"⚠️ Queue stalled: Current prompt has been running longer than expected"
        alerts.append((msg, "warning"))
        exit_code = 1

    # Send Discord alerts if webhook URL provided
    if discord_webhook_url and alerts:
        print("\nSending Discord alerts...")
        for alert_msg, severity in alerts:
            await send_discord_alert(discord_webhook_url, alert_msg, severity)
            print(f"  Sent: {alert_msg}")

    return exit_code


async def main():
    parser = ArgumentParser(description="Health check with Discord alerts")
    parser.add_argument(
        "--url",
        default=os.getenv("HEALTH_CHECK_URL", "http://localhost:8000"),
        help="Base server URL (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    # Get Discord webhook URL from environment
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

    if discord_webhook:
        print(f"Discord alerts enabled")
    else:
        print("Discord alerts disabled (set DISCORD_WEBHOOK_URL to enable)")

    print(f"Checking health at: {args.url}/api/health\n")

    exit_code = await check_health(args.url, discord_webhook)
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())

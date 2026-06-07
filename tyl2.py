"""
Telegram → Pocket Option Bot - Fixed Login + Session on Desktop
"""
import asyncio
import logging
import re
import os
from datetime import timedelta, timezone, datetime
from dataclasses import dataclass, field
from typing import Optional
from telethon import TelegramClient, events
from playwright.async_api import async_playwright

# ========================= CONFIG =========================
PO_EMAIL = os.getenv("PO_EMAIL", "joyjoyc254@gmail.com")
PO_PASSWORD = os.getenv("PO_PASSWORD", "VP3VGuyA")
TRADE_AMOUNT = 1
DEMO_MODE = True
EXPIRY_MINUTES = 5
MG_ENABLED = True
MG_MULTIPLIER = 2
MG_MAX_ROUNDS = 2

# Telegram Config
API_ID = int(os.getenv("API_ID", 29827262))
API_HASH = os.getenv("API_HASH", "f4c9b71639c8df8c27a0c50937c6460c")
PHONE = os.getenv("PHONE", "+254729698087")
CHANNEL = "TYL VIP - trading"

UTC_PLUS_1 = timezone(timedelta(hours=1))

# Save on Desktop
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
STORAGE_STATE_PATH = os.path.join(DESKTOP_PATH, "pocket_option_session.json")

# ========================= LOGGING =========================
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
log = logging.getLogger(__name__)

# ========================= SIGNAL PARSER =========================
@dataclass
class Signal:
    asset: str
    direction: str
    expiry_minutes: int = 5
    entry_time: Optional[str] = None
    martingale_times: list = field(default_factory=list)
    raw: str = ""

def parse_signal(text: str) -> Optional[Signal]:
    direction_match = re.search(r'\b(BUY|SELL|UP|DOWN)\b', text, re.IGNORECASE)
    asset_match = re.search(r'([A-Z]{3}[ /]?[A-Z]{3}(?:\s+OTC)?)', text, re.IGNORECASE)
    
    if not direction_match or not asset_match:
        return None

    direction = "BUY" if direction_match.group(1).upper() in ("BUY", "UP") else "SELL"
    raw_asset = asset_match.group(1).upper()
    search_asset = raw_asset.replace(" ", "").replace("/", "").replace("OTC", "").strip()

    expiry_match = re.search(r'expir\w*[^\d]*(\d+)\s*min', text, re.IGNORECASE)
    entry_match = re.search(r'(?:entry|trade|execute|at)\s*(\d{1,2}:\d{2})', text, re.IGNORECASE)
    mg_times = re.findall(r'martingale\s+(?:at|@)?\s*(\d{1,2}:\d{2})', text, re.IGNORECASE)

    return Signal(
        asset=search_asset,
        direction=direction,
        expiry_minutes=int(expiry_match.group(1)) if expiry_match else 5,
        entry_time=entry_match.group(1) if entry_match else None,
        martingale_times=mg_times,
        raw=text,
    )

# ========================= POCKET OPTION BOT =========================
class PocketOptionBot:
    def __init__(self):
        self.page = None
        self.pw = None
        self.browser = None
        self.context = None

    async def start(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(
            headless=False,
            args=["--start-maximized", "--no-sandbox"]
        )

        if os.path.exists(STORAGE_STATE_PATH):
            log.info(f"✅ Loading saved session from Desktop")
            self.context = await self.browser.new_context(
                viewport={"width": 1440, "height": 900},
                storage_state=STORAGE_STATE_PATH
            )
        else:
            log.info("No saved session found. Fresh login required.")
            self.context = await self.browser.new_context(
                viewport={"width": 1440, "height": 900}
            )

        self.page = await self.context.new_page()
        await self.page.goto("https://pocketoption.com/en/login/", wait_until="networkidle")
        await asyncio.sleep(5)

        if not os.path.exists(STORAGE_STATE_PATH):
            log.info("Filling login details...")
            await self.page.fill('input[name="email"]', PO_EMAIL)
            await self.page.fill('input[name="password"]', PO_PASSWORD)
            await asyncio.sleep(2)

            # IMPROVED LOGIN BUTTON CLICK
            log.info("Trying to click login button...")
            try:
                # Try multiple possible login buttons
                await self.page.click('button:has-text("Log in")', timeout=10000)
                log.info("Clicked 'Log in' button")
            except:
                try:
                    await self.page.click('button[type="submit"]', timeout=10000)
                    log.info("Clicked submit button")
                except:
                    log.info("Could not click button automatically. Please click LOGIN manually now.")

            log.info("🔴 SOLVE CAPTCHA + CLICK LOGIN MANUALLY if needed")
            await asyncio.sleep(60)   # Give enough time

            # Save session
            await self.context.storage_state(path=STORAGE_STATE_PATH)
            log.info(f"✅ Session saved to Desktop: {STORAGE_STATE_PATH}")

        # Go to trading page
        url = "https://pocketoption.com/en/cabinet/demo-quick-high-low/" if DEMO_MODE else "https://pocketoption.com/en/cabinet/quick-high-low/"
        await self.page.goto(url, wait_until="networkidle")
        await asyncio.sleep(10)
        log.info("Trading page loaded ✅")

    # [Rest of methods - select_asset, set_amount, click_direction, etc. are the same as before]

    async def set_amount(self, amount):
        try:
            log.info(f"Setting amount to {amount}...")
            amount_input = self.page.locator("xpath=/html/body/div[4]/div[2]/div[4]/div/div/div/div[1]/div/div[5]/div/div/div[2]/div/div[1]/div[2]/div[2]/div[1]/div/input")
            await amount_input.click()
            await asyncio.sleep(1)
            await self.page.keyboard.press("Control+A")
            await self.page.keyboard.press("Backspace")
            await self.page.keyboard.type(str(int(amount)))
        except Exception as e:
            log.error(f"Amount error: {e}")

    async def click_direction(self, direction):
        try:
            if direction == "BUY":
                xpath = "/html/body/div[4]/div[2]/div[4]/div/div/div/div[1]/div/div[5]/div/div/div[2]/div/div[2]/div[2]/div[1]/a/span/span/span"
                await self.page.click(f"xpath={xpath}")
                log.info("BUY (UP) TRADE PLACED")
            else:
                xpath = "/html/body/div[4]/div[2]/div[4]/div/div/div/div[1]/div/div[5]/div/div/div[2]/div/div[2]/div[2]/div[2]/a/span/span/span"
                await self.page.click(f"xpath={xpath}")
                log.info("SELL (DOWN) TRADE PLACED")
        except Exception as e:
            log.error(f"Trade click error: {e}")

    async def select_asset(self, asset):
        log.info(f"Selecting asset '{asset}'...")
        for attempt in range(1, 4):
            try:
                asset_dropdown = self.page.locator('xpath=/html/body/div[4]/div[2]/div[4]/div/div/div/div[1]/div/div[1]/div[1]/div[1]/div/a/div/span')
                await asset_dropdown.click()
                await asyncio.sleep(2)

                search_input = self.page.locator('input[placeholder="Search"]')
                await search_input.click()
                await self.page.keyboard.press("Control+A")
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(0.5)
                await search_input.type(asset, delay=100)
                await asyncio.sleep(2.5)

                await self.page.screenshot(path=f"debug_asset_search{attempt}.png")

                search_box = await search_input.bounding_box()
                if search_box:
                    result_x = search_box['x'] + search_box['width'] / 2
                    result_y = search_box['y'] + search_box['height'] + 70
                    await self.page.mouse.move(result_x, result_y)
                    await asyncio.sleep(0.5)
                    await self.page.mouse.click(result_x, result_y)
                    await asyncio.sleep(2.5)

                current_asset_text = await self.page.locator(
                    'xpath=/html/body/div[4]/div[2]/div[4]/div/div/div/div[1]/div/div[1]/div[1]/div[1]/div/a/div/span'
                ).inner_text(timeout=5000)
                
                log.info(f"Current asset displayed: '{current_asset_text}'")
                
                current_clean = current_asset_text.upper().replace("/", "").replace(" ", "").replace("OTC", "").strip()
                if asset.upper() in current_clean or current_clean in asset.upper():
                    log.info(f"✅ Asset VERIFIED: '{current_asset_text}'")
                    return True
            except Exception as e:
                log.error(f"Asset attempt {attempt} error: {e}")
            await asyncio.sleep(2)
        return False

    async def read_trade_result_fast(self):
        log.info("📖 Reading topmost closed trade result...")
        await self.page.screenshot(path="debug_trade_closed.png")
        for attempt in range(30):
            try:
                profit_el = self.page.locator(f"xpath={TOP_TRADE_PROFIT_XPATH}")
                if await profit_el.count() > 0:
                    profit_text = (await profit_el.first.inner_text()).strip()
                    if profit_text and profit_text not in ['', '-', '--', '...']:
                        result = self._parse_win_loss(profit_text)
                        if result is not None:
                            return result
                
                top_row = self.page.locator(f"xpath={TOP_TRADE_XPATH}")
                if await top_row.count() > 0:
                    row_text = (await top_row.first.inner_text()).strip()
                    if row_text and len(row_text) > 10:
                        result = self._parse_win_loss(row_text)
                        if result is not None:
                            return result
            except:
                pass
            await asyncio.sleep(0.5)
        log.error("Could not read trade result")
        return None

    def _parse_win_loss(self, text):
        if not text or text.strip() in ['', '-']:
            return None
        dollar_amounts = re.findall(r'\$\s*([\d.]+)', text)
        if len(dollar_amounts) >= 3:
            try:
                profit = float(dollar_amounts[2])
                if profit > 0:
                    log.info(f"✅ WIN detected! Profit: ${profit}")
                    return True
                elif profit == 0:
                    log.info("❌ LOSS detected")
                    return False
            except:
                pass
        if re.search(r'-\s*\$?[\d.]+', text) or re.search(r'\$\s*0(\.0+)?\s*\$\s*0', text):
            log.info("❌ LOSS detected")
            return False
        if re.search(r'\+\s*\$?[\d.]+', text):
            log.info("✅ WIN detected")
            return True
        return None

    async def stop(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()

# XPaths
CLOSED_TRADES_CONTAINER = "/html/body/div[4]/div[2]/div[4]/div/div/div/div[2]/div/div[2]/div/div[2]"
TOP_TRADE_XPATH = f"{CLOSED_TRADES_CONTAINER}/div[1]"
TOP_TRADE_PROFIT_XPATH = f"{CLOSED_TRADES_CONTAINER}/div[1]/div/div[2]/div[2]/div/div[2]/div[2]"

# HELPERS + MAIN (same as previous version)
async def wait_until_po_time(page, target_h, target_m):
    log.info(f"⏰ Waiting for {target_h:02d}:{target_m:02d}...")
    while True:
        now = datetime.now(UTC_PLUS_1)
        if now.hour == target_h and now.minute == target_m:
            log.info("✅ Target time reached!")
            return
        if now.hour * 60 + now.minute > target_h * 60 + target_m:
            log.info("Already past target time — proceeding")
            return
        await asyncio.sleep(1)

async def main():
    bot = PocketOptionBot()
    await bot.start()

    client = TelegramClient("session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    log.info("Telegram connected ✓")

    channel = None
    try:
        channel = await client.get_entity(CHANNEL)
    except Exception:
        async for dialog in client.iter_dialogs():
            if CHANNEL.lower() in dialog.name.lower():
                channel = dialog.entity
                break

    if not channel:
        log.error("Channel not found!")
        return

    @client.on(events.NewMessage(chats=channel))
    async def on_message(event):
        text = event.message.message
        if not text:
            return
        signal = parse_signal(text)
        if not signal:
            return

        log.info(f"📩 SIGNAL RECEIVED → {signal}")

        try:
            selected = await bot.select_asset(signal.asset)
            if not selected:
                log.error("Asset selection failed")
                return

            await bot.page.reload()
            await asyncio.sleep(8)
            await bot.set_amount(TRADE_AMOUNT)

            if signal.entry_time:
                try:
                    h, m = map(int, signal.entry_time.split(":"))
                    await wait_until_po_time(bot.page, h, m)
                except:
                    pass

            await bot.click_direction(signal.direction)
            log.info(f"✅ Initial trade placed: {signal.direction} ${TRADE_AMOUNT}")

            await asyncio.sleep(signal.expiry_minutes * 60)
            won = await bot.read_trade_result_fast()

            if won is True:
                log.info("🎉 Initial trade WON - No martingale")
                return
            elif won is False:
                log.info("❌ Initial trade LOST - Starting martingale")
            else:
                log.warning("Cannot determine result")
                return

            if MG_ENABLED and signal.martingale_times:
                amount = TRADE_AMOUNT
                for i, mg_time in enumerate(signal.martingale_times[:MG_MAX_ROUNDS]):
                    amount *= MG_MULTIPLIER
                    try:
                        h, m = map(int, mg_time.split(":"))
                        await wait_until_po_time(bot.page, h, m)
                    except:
                        continue

                    await bot.set_amount(amount)
                    await bot.click_direction(signal.direction)
                    log.info(f"✅ Martingale {i+1} placed: ${amount}")

                    await asyncio.sleep(signal.expiry_minutes * 60)
                    won = await bot.read_trade_result_fast()

                    if won is True:
                        log.info(f"🎉 Martingale {i+1} WON!")
                        break
                    else:
                        log.info(f"❌ Martingale {i+1} LOST")

        except Exception as e:
            log.error(f"Execution error: {e}")

    log.info("🤖 Bot is now listening for signals... (Ctrl+C to stop)")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
"""Iteration 84 — UI-driven Decoder→Create-Product flow for Workbook + Teacher Guide."""
import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

BASE = "https://enterprise-os-17.preview.emergentagent.com"


async def main():
    created_ids = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await ctx.new_page()

        page.on("console", lambda m: print(f"CONSOLE[{m.type}]: {m.text}") if m.type in ("error", "warning") else None)

        try:
            # Prime an app URL so localStorage is set for the app's origin
            await page.goto(BASE + "/", wait_until="domcontentloaded")
            await page.wait_for_timeout(1000)

            tok_resp = await page.evaluate(
                "async () => {"
                " const r = await fetch('/api/auth/login', {"
                "  method: 'POST', headers: {'Content-Type':'application/json'},"
                "  body: JSON.stringify({email:'demo.admin@qru.com', password:'qru-demo-admin-2026'})"
                " });"
                " return await r.json();"
                "}"
            )
            assert tok_resp.get("access_token"), "login failed: " + json.dumps(tok_resp)[:200]
            token = tok_resp["access_token"]
            user = tok_resp.get("user") or {}
            await page.evaluate("(t) => localStorage.setItem('qru_token', t)", token)
            await page.evaluate("(u) => localStorage.setItem('qru_user', JSON.stringify(u))", user)
            print("LOGIN OK role=" + str(user.get("role")))

            await page.goto(BASE + "/decoder-engine", wait_until="domcontentloaded")
            await page.wait_for_selector('[data-testid="ready-list"]', timeout=20000)
            print("STEP 1/2: /decoder-engine loaded")

            items = await page.query_selector_all('[data-testid^="ready-item-"]')
            print("Manufacturing Ready items: " + str(len(items)))

            chosen = None
            chosen_label = ""
            for it in items:
                lbl = (await it.inner_text()).strip()
                if "DEC-00008" in lbl or "DEC-00013" in lbl:
                    chosen = it
                    chosen_label = lbl
                    break
            if not chosen and items:
                chosen = items[0]
                chosen_label = (await items[0].inner_text()).strip()
            assert chosen, "no Manufacturing Ready items"
            print("Selected: " + chosen_label[:100].replace("\n", " | "))
            await chosen.click(force=True)
            await page.wait_for_timeout(1200)

            await page.wait_for_selector('[data-testid="create-product-cta"]', timeout=8000)
            body_text = await page.text_content("body")
            assert "Verified Knowledge Record" in body_text, "Knowledge PASS text missing"
            print("STEP 2: create-product-cta visible; Knowledge=PASS inherits verified KR")

            for product_type in ["Workbook", "Teacher Guide"]:
                await page.goto(BASE + "/decoder-engine", wait_until="domcontentloaded")
                await page.wait_for_selector('[data-testid="ready-list"]', timeout=15000)
                await page.wait_for_timeout(700)
                items = await page.query_selector_all('[data-testid^="ready-item-"]')
                seed = chosen_label[:30]
                target = None
                for it in items:
                    lbl = (await it.inner_text()).strip()
                    if seed in lbl:
                        target = it
                        break
                target = target or items[0]
                await target.click(force=True)
                await page.wait_for_selector('[data-testid="create-product-cta"]', timeout=8000)
                await page.wait_for_timeout(400)

                await page.select_option('[data-testid="create-product-type"]', product_type)
                await page.wait_for_timeout(200)
                print("STEP 3 [" + product_type + "]: product type selected")

                async with page.expect_response(
                    lambda r: "/create-product" in r.url and r.request.method == "POST",
                    timeout=90000
                ) as rp:
                    await page.click('[data-testid="create-product-btn"]', force=True)
                resp = await rp.value
                assert resp.status == 200, "create-product HTTP " + str(resp.status)
                body = await resp.json()
                assert body.get("ok") is True
                assert body.get("product_type") == product_type
                assert body.get("engine") == "publication"
                assert body.get("route") == "/products"
                assert body.get("publication_quality_applied") is True
                pid = body["id"]
                created_ids.append(pid)
                print("STEP 3 [" + product_type + "]: OK id=" + pid + " route=" + body.get("route") + " pub_quality=True")

                await page.wait_for_url("**/products**", timeout=15000)
                await page.wait_for_selector('[data-testid="product-shelf-page"]', timeout=10000)
                print("STEP 4 [" + product_type + "]: landed on /products (product-shelf-page)")

                title = body.get("title", "")
                await page.fill('[data-testid="shelf-search"]', title[:20])
                await page.wait_for_timeout(1500)
                item_sel = '[data-testid="shelf-item-' + pid + '"]'
                found = await page.query_selector(item_sel)
                if not found:
                    await page.fill('[data-testid="shelf-search"]', "")
                    await page.wait_for_timeout(400)
                    await page.fill('[data-testid="shelf-search"]', product_type)
                    await page.wait_for_timeout(1500)
                    found = await page.query_selector(item_sel)
                assert found is not None, "shelf-item-" + pid + " not found"
                print("STEP 5 [" + product_type + "]: shelf-item-" + pid + " present in My Products")
                await page.screenshot(
                    path="/app/test_reports/i84_" + product_type.replace(" ", "_") + ".jpg",
                    quality=40, full_page=False, type="jpeg"
                )

            print("CREATED_IDS=" + json.dumps(created_ids))
            os.makedirs("/app/test_reports", exist_ok=True)
            with open("/app/test_reports/.i84_created.json", "w") as f:
                json.dump({"ids": created_ids}, f)
            print("UI FLOW PASSED for Workbook and Teacher Guide")

        except Exception as e:
            print("FAIL: " + str(e))
            try:
                await page.screenshot(path="/app/test_reports/i84_error.jpg", quality=40, full_page=False, type="jpeg")
            except Exception:
                pass
            with open("/app/test_reports/.i84_created.json", "w") as f:
                json.dump({"ids": created_ids}, f)
            raise
        finally:
            await ctx.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

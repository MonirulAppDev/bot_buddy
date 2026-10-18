import asyncio
import sys
import uuid

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import init_db, AsyncSessionLocal
from app.models.fb_account import FBAccount
from app.models.fb_page import FBPage
from sqlalchemy import select

PARENT_BOTS = [
    {
        "name": "Alex Turner (Alpha Bot)",
        "uid": "100088112233",
        "cookie": "c_user=100088112233; xs=38%3Aalpha_token_998877; fr=alpha_fr_01;",
        "pages": [
            ("Silicon Valley Tech Daily", "Digital Creator"),
            ("Dhaka Street Food Chronicles", "Community"),
            ("Pro Gamerz Hub", "Entertainment"),
            ("Viral Memes & Vibe", "Media/News"),
            ("Fitness & Workout Nation", "Personal Blog")
        ]
    },
    {
        "name": "Sophia Bennett (Beta Bot)",
        "uid": "100077223344",
        "cookie": "c_user=100077223344; xs=38%3Abeta_token_887766; fr=beta_fr_02;",
        "pages": [
            ("Cinematic Universe Daily", "Entertainment"),
            ("Global Travel Insider", "Personal Blog"),
            ("Crypto Bulls & News", "Financial Service"),
            ("Photography & Art Zone", "Art"),
            ("Football Passion 24/7", "Sports")
        ]
    },
    {
        "name": "Liam Miller (Gamma Bot)",
        "uid": "100066334455",
        "cookie": "c_user=100066334455; xs=38%3Agamma_token_776655; fr=gamma_fr_03;",
        "pages": [
            ("NextGen AI & Robotics", "Science/Tech"),
            ("Daily Motivation Pulse", "Community"),
            ("Gadget Review Lab", "Digital Creator"),
            ("Acoustic Beats Lounge", "Music"),
            ("City Pulse Today", "News")
        ]
    }
]


async def seed():
    print("Initializing TiDB Cloud database tables...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        res = await session.execute(select(FBAccount))
        existing = res.scalars().all()
        
        created_accounts = 0
        created_pages = 0

        for bot_data in PARENT_BOTS:
            # Check if this bot exists
            existing_bot = next((b for b in existing if b.fb_user_id == bot_data["uid"]), None)
            if not existing_bot:
                acc = FBAccount(
                    id=str(uuid.uuid4()),
                    account_name=bot_data["name"],
                    cookie_data=bot_data["cookie"],
                    fb_user_id=bot_data["uid"],
                    status="active",
                    total_likes_given=0
                )
                session.add(acc)
                await session.flush()
                created_accounts += 1
                parent_id = acc.id
            else:
                parent_id = existing_bot.id

            # Add pages for this bot
            for page_name, category in bot_data["pages"]:
                page_res = await session.execute(select(FBPage).where(FBPage.page_name == page_name))
                if not page_res.scalars().first():
                    new_page = FBPage(
                        id=str(uuid.uuid4()),
                        parent_account_id=parent_id,
                        page_name=page_name,
                        category=category,
                        avatar_url=f"https://api.dicebear.com/7.x/identicon/svg?seed={page_name.replace(' ', '')}",
                        status="active",
                        total_likes_given=0
                    )
                    session.add(new_page)
                    created_pages += 1

        await session.commit()
        print(f"TiDB Cloud Seed Completed! Added {created_accounts} Parent Bots and {created_pages} Sub-Pages! 🚀")


if __name__ == "__main__":
    asyncio.run(seed())

import random
import uuid
from faker import Faker
from app.models.persona import Persona


AVATAR_SOURCES = [
    "https://i.pravatar.cc/300?u=",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=",
    "https://api.dicebear.com/7.x/personas/svg?seed="
]


def generate_single_persona(locale: str = "en_US", platform: str = "facebook") -> Persona:
    """Generate a single realistic dummy persona with localized name, username, and avatar."""
    try:
        fake = Faker(locale)
    except Exception:
        fake = Faker("en_US")
        locale = "en_US"

    first_name = fake.first_name()
    last_name = fake.last_name()
    display_name = f"{first_name} {last_name}"
    
    # Generate realistic social handle
    discriminator = random.randint(10, 9999)
    clean_first = "".join(filter(str.isalnum, first_name.lower()))
    clean_last = "".join(filter(str.isalnum, last_name.lower()))
    username = f"{clean_first}_{clean_last}_{discriminator}"

    persona_id = str(uuid.uuid4())
    avatar_base = random.choice(AVATAR_SOURCES)
    avatar_url = f"{avatar_base}{persona_id}"

    bio = fake.catch_phrase() if hasattr(fake, "catch_phrase") else "Living life to the fullest!"
    
    extra = {
        "bio": bio,
        "city": fake.city() if hasattr(fake, "city") else "Dhaka",
        "country": fake.country() if hasattr(fake, "country") else "Bangladesh",
        "gender": random.choice(["male", "female", "other"]),
        "account_age_months": random.randint(3, 48),
        "reputation_score": round(random.uniform(0.75, 0.99), 2)
    }

    import json
    return Persona(
        id=persona_id,
        username=username,
        display_name=display_name,
        avatar_url=avatar_url,
        platform=platform,
        locale=locale,
        status="active",
        total_actions=0,
        extra_metadata=json.dumps(extra)
    )


def generate_personas_batch(count: int = 10, locale: str = "en_US", platform: str = "facebook") -> list[Persona]:
    """Generate multiple realistic dummy personas."""
    return [generate_single_persona(locale=locale, platform=platform) for _ in range(count)]

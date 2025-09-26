"""
Database seed script.
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.destination import Destination
from app.models.knowledge_base import KnowledgeBase, KnowledgeScope
from app.core.security import get_password_hash
import uvloop


async def seed_data():
    """Seed the database with initial data."""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        session: AsyncSession = session
        # Create a default organization
        org_name = "Default Organization"
        organization = await session.execute(select(Organization).where(Organization.name == org_name))
        organization = organization.scalar_one_or_none()
        if not organization:
            organization = Organization(name=org_name)
            session.add(organization)
            await session.commit()
            await session.refresh(organization)

        # Create a default user
        email = "admin@example.com"
        user = await session.execute(select(User).where(User.email == email))
        user = user.scalar_one_or_none()
        if not user:
            user = User(
                email=email,
                password_hash=get_password_hash("admin"),
                # first_name="Admin",
                # last_name="User",
                role=UserRole.ADMIN.value,
                org_id=organization.id,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # Create destinations
        destinations_to_create = [
            {"name": "Paris", "description": "The city of lights."},
            {"name": "Tokyo", "description": "A vibrant metropolis."},
            {"name": "New York", "description": "The city that never sleeps."},
        ]

        for dest_data in destinations_to_create:
            destination = await session.execute(select(Destination).where(Destination.name == dest_data["name"], Destination.org_id == organization.id))
            destination = destination.scalar_one_or_none()
            if not destination:
                destination = Destination(
                    name=dest_data["name"],
                    description=dest_data["description"],
                    org_id=organization.id,
                    user_id=user.id,
                )
                session.add(destination)
        await session.flush()

        # Add knowledge to Paris
        paris = await session.execute(select(Destination).where(Destination.name == "Paris", Destination.org_id == organization.id))
        paris = paris.scalar_one_or_none()
        if paris:
            knowledge_items = [
                {"title": "Eiffel Tower", "scope": KnowledgeScope.ORG_PUBLIC.value},
                {"title": "Louvre Museum", "scope": KnowledgeScope.ORG_PUBLIC.value},
                {"title": "Notre-Dame Cathedral", "scope": KnowledgeScope.ORG_PUBLIC.value},
                {"title": "Best croissant spots", "scope": KnowledgeScope.PRIVATE.value},
            ]
            for item in knowledge_items:
                kb_item = await session.execute(select(KnowledgeBase).where(KnowledgeBase.title == item["title"], KnowledgeBase.destination_id == paris.id))
                kb_item = kb_item.scalar_one_or_none()
                if not kb_item:
                    kb_item = KnowledgeBase(
                        title=item["title"],
                        scope=item["scope"],
                        org_id=organization.id,
                        user_id=user.id,
                        destination_id=paris.id,
                    )
                    session.add(kb_item)
            await session.commit()

    await engine.dispose()
    print("Database seeded successfully!")


if __name__ == "__main__":
    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(seed_data())

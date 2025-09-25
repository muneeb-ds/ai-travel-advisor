from uuid import UUID
import logging
import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.ext.asyncio.engine import AsyncEngine
# from sqlalchemy.ext.asyncio import Async
# from sqlalchemy import inspect

logger = logging.getLogger(__name__)


class OpsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def get_metrics(self, user_id: UUID) -> dict:
        return {"metrics": "metrics"}

    async def _check_outbound_connectivity(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                response = await client.head(url)
                response.raise_for_status()
            return "healthy"
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning(f"Outbound check for {url} failed: {e}")
            return "unhealthy"

    async def get_healthz(self) -> dict:
        db_status = "healthy"
        embeddings_table_status = "healthy"
        
        # Check database connectivity
        try:
            await self.db.execute(text("SELECT 1"))
        except Exception:
            db_status = "unhealthy"
        
        # Check for embeddings table
        try:
            result = await self.db.execute(text("SELECT to_regclass('public.embeddings')"))
            embeddings_table_status = "healthy" if result.scalar() is not None else "unhealthy"

        except Exception as e:
            logger.exception(e)
            embeddings_table_status = "unhealthy" 
            
        # Check outbound connectivity
        open_meteo_status = await self._check_outbound_connectivity("https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true")
        nominatim_status = await self._check_outbound_connectivity("https://nominatim.openstreetmap.org/ui/search.html")

        is_healthy = all(status == "healthy" for status in [db_status, embeddings_table_status, open_meteo_status, nominatim_status])
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "checks": {
                "database": db_status,
                "embeddings_table": embeddings_table_status,
                "open_meteo": open_meteo_status,
                "nominatim": nominatim_status,
            },
        }

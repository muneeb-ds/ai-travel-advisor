from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

from app.core.settings import settings


async def get_embedding_pgvector_db_store() -> PGVectorStore:
    pgvector_db_engine = PGEngine.from_connection_string(settings.DATABASE_URL)

    # Set an existing table name
    TABLE_NAME = "embeddings"

    pgvector_db_store = await PGVectorStore.create(
        engine=pgvector_db_engine,
        table_name=TABLE_NAME,
        embedding_service=OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY),
        # Connect to existing VectorStore by customizing below column names
        id_column="id",
        content_column="content",
        embedding_column="embedding",
        metadata_columns=["knowledge_item_id", "chunk_idx", "created_at", "title"],
    )
    return pgvector_db_store

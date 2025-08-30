# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# (EN) The connection URL for our async SQLite database.
# (ES) La URL de conexión para nuestra base de datos SQLite asíncrona.
DATABASE_URL = "sqlite+aiosqlite:///./cache.db"

# (EN) Create the async engine.
# (ES) Creamos el motor asíncrono.
engine = create_async_engine(DATABASE_URL, echo=True)

# (EN) Create a session factory for creating new async sessions.
# (ES) Creamos una factoría de sesiones para crear nuevas sesiones asíncronas.
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# (EN) A base class for our declarative models.
# (ES) Una clase base para nuestros modelos declarativos.
Base = declarative_base()
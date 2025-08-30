# app/services/workspace.py
import os
from pathlib import Path
import shutil
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models import Source, SourceCache

class WorkspaceService:
    """
    (EN) Manages the creation and caching of execution workspaces.
    (ES) Gestiona la creación y el cacheo de los espacios de trabajo.
    """
    def __init__(self, root_dir: str = "appdroid_workspaces"):
        self.root_workspace_dir = Path(root_dir)
        self.root_workspace_dir.mkdir(exist_ok=True)

    async def prepare_workspace(self, session: AsyncSession, env_name: str, source: Source) -> Path:
        """
        (EN) Ensures a workspace exists for the given source, using a cache.
        (ES) Asegura que exista un espacio de trabajo para el origen dado, usando un caché.
        """
        result = await session.execute(select(SourceCache).where(SourceCache.uri == source.uri))
        cached_source = result.scalar_one_or_none()

        workspace_path = self.root_workspace_dir / env_name

        if cached_source:
            print(f"INFO:     Cache HIT for source: {source.uri}")
            # (EN) In a real scenario with Git, we would 'git pull' here.
            # (ES) En un escenario real con Git, aquí haríamos 'git pull'.
            cached_source.last_updated = datetime.datetime.utcnow()
            await session.commit()
            return Path(cached_source.local_path)
        else:
            print(f"INFO:     Cache MISS for source: {source.uri}. Creating workspace...")
            workspace_path.mkdir(exist_ok=True)
            
            # (EN) For now, we only handle the 'file' type.
            # (ES) Por ahora, solo manejamos el tipo 'file'.
            if source.type == "file":
                source_file = Path(source.uri)
                dest_file = workspace_path / source_file.name
                shutil.copy(source_file, dest_file)
            else:
                # (EN) Logic for 'git clone' would go here.
                # (ES) La lógica para 'git clone' iría aquí.
                raise NotImplementedError("Source type 'git' is not yet implemented.")

            # (EN) Save the new entry to the cache database.
            # (ES) Guardamos la nueva entrada en la base de datos del caché.
            new_cache_entry = SourceCache(uri=source.uri, local_path=str(workspace_path))
            session.add(new_cache_entry)
            await session.commit()
            return workspace_path
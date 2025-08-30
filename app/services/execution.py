# app/services/execution.py
import asyncio
from pathlib import Path
from typing import List

from ..models import ScriptManifest

class ScriptExecutionService:
    """
    (EN) Manages Conda environments and executes external scripts.
    (ES) Gestiona los entornos de Conda y ejecuta scripts externos.
    """
    async def run_script(self, manifest: ScriptManifest, workspace_path: Path, task_id: str):
        """
        (EN) Orchestrates the environment setup and execution of a script.
        (ES) Orquesta la configuración del entorno y la ejecución de un script.
        """
        env_name = manifest.environment_name
        await self._ensure_environment_exists(env_name)
        
        if manifest.dependencies and manifest.dependencies.packages:
            await self._install_dependencies(env_name, manifest.dependencies.packages)

        script_file_path = workspace_path / manifest.execution.script
        
        args_str = " ".join(f'"{arg}"' for arg in manifest.execution.args)
        command = (
            f"conda run -n {env_name} "
            f"{manifest.execution.command} {script_file_path} {task_id} {args_str}"
        )

        print(f"INFO:     [{task_id}] Executing command: {command}")

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            print(f"INFO:     [{task_id}] Script finished successfully.")
        else:
            print(f"ERROR:    [{task_id}] Script failed with exit code {process.returncode}.")
            print(f"STDERR:   {stderr.decode()}")


    async def _run_command(self, command: str) -> bool:
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            print(f"ERROR:    Command failed: {command}\n{stderr.decode()}")
            return False
        return True

    async def _ensure_environment_exists(self, env_name: str):
        print(f"INFO:     Verifying Conda environment: {env_name}")
        # (EN) This is a simplified check. A more robust one would parse the JSON output.
        # (ES) Esta es una comprobación simplificada. Una más robusta parsearía la salida JSON.
        process = await asyncio.create_subprocess_shell("conda env list", stdout=asyncio.subprocess.PIPE)
        stdout, _ = await process.communicate()
        if env_name not in stdout.decode():
            print(f"WARN:     Conda environment '{env_name}' not found. Creating...")
            await self._run_command(f"conda create --name {env_name} python=3.9 -y")

    async def _install_dependencies(self, env_name: str, packages: List[str]):
        packages_str = " ".join(packages)
        print(f"INFO:     Installing dependencies in '{env_name}': {packages_str}")
        await self._run_command(f"conda install --name {env_name} -c conda-forge {packages_str} -y")
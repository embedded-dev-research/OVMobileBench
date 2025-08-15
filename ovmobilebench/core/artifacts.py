"""Artifact management utilities."""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from ovmobilebench.core.fs import ensure_dir, atomic_write


class ArtifactManager:
    """Manage build and benchmark artifacts."""

    def __init__(self, base_dir: Path):
        """Initialize artifact manager.

        Args:
            base_dir: Base directory for artifacts
        """
        self.base_dir = Path(base_dir)
        self.build_dir = ensure_dir(self.base_dir / "build")
        self.packages_dir = ensure_dir(self.base_dir / "packages")
        self.results_dir = ensure_dir(self.base_dir / "results")
        self.logs_dir = ensure_dir(self.base_dir / "logs")
        self.metadata_file = self.base_dir / "metadata.json"

    def get_build_path(self, platform: str, commit: str) -> Path:
        """Get path for build artifacts.

        Args:
            platform: Target platform (android, linux)
            commit: Git commit hash

        Returns:
            Path to build directory
        """
        return ensure_dir(self.build_dir / f"{platform}_{commit[:8]}")

    def get_package_path(self, name: str, version: str) -> Path:
        """Get path for package.

        Args:
            name: Package name
            version: Package version

        Returns:
            Path to package file
        """
        return self.packages_dir / f"{name}_{version}.tar.gz"

    def get_results_path(self, run_id: str) -> Path:
        """Get path for benchmark results.

        Args:
            run_id: Benchmark run identifier

        Returns:
            Path to results directory
        """
        return ensure_dir(self.results_dir / run_id)

    def get_log_path(self, run_id: str, stage: str) -> Path:
        """Get path for stage logs.

        Args:
            run_id: Run identifier
            stage: Pipeline stage name

        Returns:
            Path to log file
        """
        return ensure_dir(self.logs_dir / run_id) / f"{stage}.log"

    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save artifact metadata.

        Args:
            metadata: Metadata dictionary
        """
        metadata["updated_at"] = datetime.utcnow().isoformat()

        # Load existing metadata
        existing = self.load_metadata()
        existing.update(metadata)

        # Save atomically
        content = json.dumps(existing, indent=2, default=str)
        atomic_write(self.metadata_file, content)

    def load_metadata(self) -> Dict[str, Any]:
        """Load artifact metadata.

        Returns:
            Metadata dictionary
        """
        if not self.metadata_file.exists():
            return {}

        with open(self.metadata_file, "r") as f:
            data: Dict[str, Any] = json.load(f)
            return data

    def register_artifact(
        self, artifact_type: str, path: Path, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register new artifact.

        Args:
            artifact_type: Type of artifact (build, package, result)
            path: Path to artifact
            metadata: Optional metadata

        Returns:
            Artifact ID
        """
        # Calculate checksum
        artifact_id = self._calculate_checksum(path)

        # Prepare artifact record
        record: Dict[str, Any] = {
            "type": artifact_type,
            "path": str(path.relative_to(self.base_dir)),
            "size": path.stat().st_size if path.is_file() else None,
            "created_at": datetime.utcnow().isoformat(),
            "checksum": artifact_id,
        }

        if metadata:
            record["metadata"] = metadata

        # Save to metadata
        artifacts = self.load_metadata().get("artifacts", {})
        artifacts[artifact_id] = record
        self.save_metadata({"artifacts": artifacts})

        return artifact_id

    def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get artifact by ID.

        Args:
            artifact_id: Artifact identifier

        Returns:
            Artifact record or None
        """
        artifacts = self.load_metadata().get("artifacts", {})
        result: Optional[Dict[str, Any]] = artifacts.get(artifact_id)
        return result

    def list_artifacts(
        self, artifact_type: Optional[str] = None, since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """List artifacts.

        Args:
            artifact_type: Filter by type
            since: Filter by creation time

        Returns:
            List of artifact records
        """
        artifacts = self.load_metadata().get("artifacts", {})
        results = []

        for aid, record in artifacts.items():
            # Apply filters
            if artifact_type and record.get("type") != artifact_type:
                continue

            if since:
                created = datetime.fromisoformat(record["created_at"])
                if created < since:
                    continue

            record["id"] = aid
            results.append(record)

        # Sort by creation time
        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results

    def cleanup_old_artifacts(self, days: int = 30) -> int:
        """Clean up old artifacts.

        Args:
            days: Keep artifacts newer than this many days

        Returns:
            Number of artifacts removed
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        artifacts = self.load_metadata().get("artifacts", {})
        to_remove = []

        for aid, record in artifacts.items():
            created = datetime.fromisoformat(record["created_at"])
            if created < cutoff:
                # Remove physical artifact
                artifact_path = self.base_dir / record["path"]
                if artifact_path.exists():
                    if artifact_path.is_dir():
                        import shutil

                        shutil.rmtree(artifact_path)
                    else:
                        artifact_path.unlink()

                to_remove.append(aid)

        # Update metadata
        for aid in to_remove:
            del artifacts[aid]

        self.save_metadata({"artifacts": artifacts})
        return len(to_remove)

    def _calculate_checksum(self, path: Path, algorithm: str = "sha256") -> str:
        """Calculate checksum for artifact.

        Args:
            path: Path to artifact
            algorithm: Hash algorithm

        Returns:
            Hex digest
        """
        hasher = hashlib.new(algorithm)

        if path.is_file():
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
        else:
            # For directories, hash the path and modification time
            hasher.update(str(path).encode())
            hasher.update(str(path.stat().st_mtime).encode())

        return hasher.hexdigest()[:16]  # Use first 16 chars for ID

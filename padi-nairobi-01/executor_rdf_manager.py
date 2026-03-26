#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🏛️ PADI EXECUTOR v5.3 — RDF Snapshot Manager
==================================================

Component:
- RDFSnapshotManager: Comprehensive RDF graph snapshot management for audit trail

Features:
- Full graph serialization (Turtle, JSON-LD, N-Triples)
- Efficient storage with deduplication
- Timestamped indexing for historical queries
- Export functionality for compliance
- Query capability for post-hoc analysis

Version: 5.3
Node: Nairobi-01
Timestamp: 2026-03-26 [EAT]
"""

import threading
import hashlib
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from rdflib import Graph
import logging

logger = logging.getLogger("PADI-RDF-MANAGER")


# =====================================================
# Log Directory Setup
# =====================================================

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True, parents=True)


# =====================================================
# RDF Snapshot Manager
# =====================================================

class RDFSnapshotManager:
    """
    Comprehensive RDF graph snapshot management for audit trail.
    
    Features:
    - Full graph serialization (Turtle, JSON-LD, N-Triples)
    - Efficient storage with deduplication
    - Timestamped indexing for historical queries
    - Export functionality for compliance
    - Query capability for post-hoc analysis
    
    Args:
        executor_logger: Logger instance for operations
    """
    
    def __init__(self, executor_logger: logging.Logger):
        self.logger = executor_logger
        
        self.snapshots: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
        self.dedup_cache: Dict[str, datetime] = {}
        
        self.config = {
            "max_snapshots_in_memory": 1000,
            "auto_export_interval": 100,
            "default_format": "turtle",
            "export_formats": ["turtle", "json-ld", "n-triples"]
        }
        
        self.stats = {
            "total_snapshots": 0,
            "total_deduplicated": 0,
            "total_exports": 0,
            "total_bytes_written": 0
        }
        
        self._export_counter = 0

    def set_config(self, config: Dict[str, Any]):
        """
        Update configuration.
        
        Args:
            config: Dictionary of configuration overrides
        """
        self.config.update(config)
        logger.info(f"📦 RDF Manager config updated: {self.config}")

    def store_snapshot(
        self,
        graph: Graph,
        graph_id: Optional[str] = None,
        signal_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store an RDF graph snapshot with full metadata.
        
        Args:
            graph: RDFLib Graph object
            graph_id: Optional graph identifier (auto-generated if None)
            signal_id: Associated signal ID
            metadata: Additional metadata dictionary
        
        Returns:
            Snapshot ID
        """
        timestamp = datetime.now()
        
        if not graph_id:
            graph_id = f"graph_{len(self.snapshots)}_{int(timestamp.timestamp())}"
        
        graph_hash = self._calculate_graph_hash(graph)
        if graph_hash in self.dedup_cache:
            self.logger.info(f"🔍 Duplicate graph detected: {graph_id}")
            self.stats["total_deduplicated"] += 1
            return graph_id
        
        self.dedup_cache[graph_hash] = timestamp
        
        serializations = {}
        for fmt in self.config["export_formats"]:
            try:
                serializations[fmt] = graph.serialize(format=fmt)
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to serialize {fmt}: {e}")
                serializations[fmt] = b""
        
        snapshot = {
            "snapshot_id": graph_id,
            "timestamp": timestamp.isoformat(),
            "signal_id": signal_id,
            "metadata": metadata or {},
            "serializations": serializations,
            "triple_count": len(graph),
            "bytes_size": sum(len(data) for data in serializations.values()),
            "graph_hash": graph_hash
        }
        
        with self.lock:
            self.snapshots.append(snapshot)
            self.stats["total_snapshots"] += 1
            self.stats["total_bytes_written"] += snapshot["bytes_size"]
            
            if len(self.snapshots) > self.config["max_snapshots_in_memory"]:
                self.snapshots = self.snapshots[-self.config["max_snapshots_in_memory"]:]
        
        self.logger.info(
            f"📸 Snapshot stored: {graph_id} | Triples: {snapshot['triple_count']} | "
            f"Size: {snapshot['bytes_size']} bytes"
        )
        
        self._export_counter += 1
        if self._export_counter >= self.config["auto_export_interval"]:
            self.export_snapshot("auto_export")
            self._export_counter = 0
        
        return graph_id

    def _calculate_graph_hash(self, graph: Graph) -> str:
        """
        Calculate a hash of the graph for deduplication.
        
        Args:
            graph: RDFLib Graph object
        
        Returns:
            SHA256 hash string
        """
        nt_data = graph.serialize(format="nt")
        if isinstance(nt_data, str):
            nt_data = nt_data.encode('utf-8')
        return hashlib.sha256(nt_data).hexdigest()

    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a snapshot by ID.
        
        Args:
            snapshot_id: Snapshot identifier
        
        Returns:
            Snapshot dictionary or None
        """
        with self.lock:
            for snapshot in self.snapshots:
                if snapshot["snapshot_id"] == snapshot_id:
                    return snapshot
        return None

    def get_snapshots_by_signal(self, signal_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all snapshots for a specific signal.
        
        Args:
            signal_id: Signal identifier
        
        Returns:
            List of snapshot dictionaries
        """
        with self.lock:
            return [
                snapshot for snapshot in self.snapshots
                if snapshot.get("signal_id") == signal_id
            ]

    def get_snapshots_by_time_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[Dict[str, Any]]:
        """
        Retrieve snapshots within a time range.
        
        Args:
            start: Start datetime
            end: End datetime
        
        Returns:
            List of snapshot dictionaries
        """
        with self.lock:
            return [
                snapshot for snapshot in self.snapshots
                if start <= datetime.fromisoformat(snapshot["timestamp"]) <= end
            ]

    def export_snapshot(
        self,
        export_id: str,
        format: str = "json",
        filepath: Optional[Path] = None
    ) -> Path:
        """
        Export snapshots to file for compliance.
        
        Args:
            export_id: Identifier for this export (used in filename)
            format: Export format ("json", "csv", "ttl")
            filepath: Optional custom filepath
        
        Returns:
            Path to exported file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if not filepath:
            if format in ["ttl", "turtle"]:
                export_dir = LOGS_DIR / "rdf_exports"
                export_dir.mkdir(exist_ok=True, parents=True)
                filepath = export_dir / f"snapshots_{export_id}_{timestamp}.ttl"
            elif format == "csv":
                export_dir = LOGS_DIR / "csv_exports"
                export_dir.mkdir(exist_ok=True, parents=True)
                filepath = export_dir / f"snapshots_{export_id}_{timestamp}.csv"
            else:
                export_dir = LOGS_DIR / "json_exports"
                export_dir.mkdir(exist_ok=True, parents=True)
                filepath = export_dir / f"snapshots_{export_id}_{timestamp}.json"
        
        try:
            if format == "json":
                self._export_json(filepath)
            elif format in ["ttl", "turtle"]:
                self._export_ttl(filepath)
            elif format == "csv":
                self._export_csv(filepath)
            
            self.stats["total_exports"] += 1
            self.logger.info(f"📄 Exported snapshots to: {filepath}")
            
        except Exception as e:
            self.logger.error(f"❌ Export failed: {e}")
            raise
        
        return filepath

    def _export_json(self, filepath: Path):
        """Export snapshots as JSON."""
        with self.lock:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "export_id": filepath.stem,
                "snapshot_count": len(self.snapshots),
                "statistics": self.stats,
                "snapshots": self.snapshots
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)

    def _export_ttl(self, filepath: Path):
        """Export snapshots as Turtle RDF."""
        with self.lock:
            combined_graph = Graph()
            
            for snapshot in self.snapshots:
                try:
                    ttl_data = snapshot["serializations"].get("turtle", b"")
                    if isinstance(ttl_data, str):
                        ttl_data = ttl_data.encode('utf-8')
                    
                    temp_graph = Graph().parse(data=ttl_data, format="turtle")
                    combined_graph += temp_graph
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to merge snapshot: {e}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(combined_graph.serialize(format="turtle"))

    def _export_csv(self, filepath: Path):
        """Export snapshot metadata as CSV."""
        with self.lock:
            fieldnames = [
                "snapshot_id", "timestamp", "signal_id", "triple_count",
                "bytes_size", "graph_hash"
            ]
            
            rows = []
            for snapshot in self.snapshots:
                row = {
                    "snapshot_id": snapshot["snapshot_id"],
                    "timestamp": snapshot["timestamp"],
                    "signal_id": snapshot.get("signal_id", ""),
                    "triple_count": snapshot["triple_count"],
                    "bytes_size": snapshot["bytes_size"],
                    "graph_hash": snapshot["graph_hash"]
                }
                rows.append(row)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def query_snapshots(
        self,
        query_func: Callable[[Dict[str, Any]], bool]
    ) -> List[Dict[str, Any]]:
        """
        Query snapshots using a custom filter function.
        
        Args:
            query_func: Function that takes a snapshot and returns bool
        
        Returns:
            List of matching snapshots
        """
        with self.lock:
            return [
                snapshot for snapshot in self.snapshots
                if query_func(snapshot)
            ]

    def clear_snapshots(
        self,
        before: Optional[datetime] = None
    ) -> int:
        """
        Clear snapshots, optionally before a certain timestamp.
        
        Args:
            before: Clear only snapshots before this timestamp
        
        Returns:
            Number of snapshots cleared
        """
        with self.lock:
            if before:
                original_count = len(self.snapshots)
                self.snapshots = [
                    snapshot for snapshot in self.snapshots
                    if datetime.fromisoformat(snapshot["timestamp"]) >= before
                ]
                cleared = original_count - len(self.snapshots)
            else:
                cleared = len(self.snapshots)
                self.snapshots = []
        
        self.logger.info(f"🗑️ Cleared {cleared} snapshots")
        return cleared

    def get_stats(self) -> Dict[str, Any]:
        """
        Get snapshot statistics.
        
        Returns:
            Dictionary of statistics
        """
        with self.lock:
            return {
                **self.stats,
                "currently_stored": len(self.snapshots),
                "dedup_cache_size": len(self.dedup_cache),
                "auto_export_counter": self._export_counter,
                "config": self.config
            }

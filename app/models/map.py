from typing import Dict, Any, List, Optional


class MapMarkerModel:
    """In-memory storage for map markers"""
    
    def __init__(self):
        self._markers: List[Dict[str, Any]] = []
    
    def add_marker(self, marker_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new marker to the map"""
        self._markers.append(marker_data)
        return marker_data
    
    def get_markers(self) -> List[Dict[str, Any]]:
        """Get all map markers"""
        return self._markers.copy()
    
    def delete_marker(self, marker_id: str) -> bool:
        """Delete a map marker by ID. Returns True if deleted, False if not found"""
        original_length = len(self._markers)
        self._markers = [m for m in self._markers if m.get("id") != marker_id]
        return len(self._markers) < original_length
    
    def get_marker_by_id(self, marker_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific marker by ID"""
        for marker in self._markers:
            if marker.get("id") == marker_id:
                return marker
        return None


# Global instance for in-memory storage
map_markers = MapMarkerModel()

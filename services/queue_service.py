import logging
from typing import List, Dict, Optional, Any
import random
from models.track import Track

logger = logging.getLogger(__name__)

class QueueService:
    def __init__(self):
        # Queue data by chat_id
        self.queues: Dict[int, List[Track]] = {}
        self.current_tracks: Dict[int, Optional[Track]] = {}
        self.history: Dict[int, List[Track]] = {}
        self.loop_modes: Dict[int, str] = {}  # none, single, all
        self.shuffle_modes: Dict[int, bool] = {}
    
    def get_queue(self, chat_id: int) -> List[Track]:
        """Get the queue for a specific chat"""
        return self.queues.get(chat_id, [])
    
    def add_to_queue(self, chat_id: int, track: Track) -> bool:
        """Add a track to the queue for a specific chat"""
        if chat_id not in self.queues:
            self.queues[chat_id] = []
        
        self.queues[chat_id].append(track)
        return True
    
    def add_tracks_to_queue(self, chat_id: int, tracks: List[Track]) -> int:
        """Add multiple tracks to the queue and return the number added"""
        if chat_id not in self.queues:
            self.queues[chat_id] = []
        
        self.queues[chat_id].extend(tracks)
        return len(tracks)
    
    def clear_queue(self, chat_id: int) -> bool:
        """Clear the queue for a specific chat"""
        self.queues[chat_id] = []
        return True
    
    def remove_from_queue(self, chat_id: int, index: int) -> Optional[Track]:
        """Remove a track at a specific index from the queue"""
        if chat_id not in self.queues or index >= len(self.queues[chat_id]) or index < 0:
            return None
        
        return self.queues[chat_id].pop(index)
    
    def move_in_queue(self, chat_id: int, old_index: int, new_index: int) -> bool:
        """Move a track from one position to another in the queue"""
        if chat_id not in self.queues:
            return False
        
        queue = self.queues[chat_id]
        if old_index < 0 or old_index >= len(queue) or new_index < 0 or new_index >= len(queue):
            return False
        
        track = queue.pop(old_index)
        queue.insert(new_index, track)
        return True
    
    def get_next_track(self, chat_id: int) -> Optional[Track]:
        """Get the next track from the queue, considering loop and shuffle settings"""
        if chat_id not in self.queues or not self.queues[chat_id]:
            return None
        
        # Handle single track loop
        loop_mode = self.get_loop_mode(chat_id)
        if loop_mode == "single" and chat_id in self.current_tracks and self.current_tracks[chat_id]:
            # Return the current track again
            return self.current_tracks[chat_id]
        
        # Get and remove the next track from the queue
        next_track = self.queues[chat_id].pop(0)
        
        # Add current track to history
        if chat_id in self.current_tracks and self.current_tracks[chat_id]:
            self._add_to_history(chat_id, self.current_tracks[chat_id])
        
        # Set as current track
        self.current_tracks[chat_id] = next_track
        
        # Handle queue looping
        if loop_mode == "all" and next_track:
            # Add the track back to the end of the queue
            self.queues[chat_id].append(next_track)
        
        return next_track
    
    def get_current_track(self, chat_id: int) -> Optional[Track]:
        """Get the currently playing track for a chat"""
        return self.current_tracks.get(chat_id)
    
    def get_history(self, chat_id: int, limit: int = 10) -> List[Track]:
        """Get the playback history for a chat"""
        history = self.history.get(chat_id, [])
        return history[:limit]
    
    def _add_to_history(self, chat_id: int, track: Track, max_history: int = 50) -> None:
        """Add a track to the history for a chat"""
        if chat_id not in self.history:
            self.history[chat_id] = []
        
        # Add to the beginning of history
        self.history[chat_id].insert(0, track)
        
        # Trim history if needed
        if len(self.history[chat_id]) > max_history:
            self.history[chat_id] = self.history[chat_id][:max_history]
    
    def get_previous_track(self, chat_id: int) -> Optional[Track]:
        """Get the previous track from history"""
        if chat_id not in self.history or len(self.history[chat_id]) < 1:
            return None
        
        # Get the previous track (index 0 is the current track)
        if len(self.history[chat_id]) > 1:
            prev_track = self.history[chat_id][1]
        else:
            prev_track = self.history[chat_id][0]
        
        # Add current track back to the beginning of queue
        if chat_id in self.current_tracks and self.current_tracks[chat_id]:
            if chat_id not in self.queues:
                self.queues[chat_id] = []
            
            self.queues[chat_id].insert(0, self.current_tracks[chat_id])
        
        # Set previous track as current
        self.current_tracks[chat_id] = prev_track
        
        # Remove from history
        if prev_track in self.history[chat_id]:
            self.history[chat_id].remove(prev_track)
        
        return prev_track
    
    def set_loop_mode(self, chat_id: int, mode: str) -> str:
        """Set the loop mode for a chat (none, single, all)"""
        if mode not in ["none", "single", "all"]:
            mode = "none"
        
        self.loop_modes[chat_id] = mode
        return mode
    
    def get_loop_mode(self, chat_id: int) -> str:
        """Get the current loop mode for a chat"""
        return self.loop_modes.get(chat_id, "none")
    
    def toggle_loop_mode(self, chat_id: int) -> str:
        """Toggle the loop mode for a chat (none -> single -> all -> none)"""
        current_mode = self.get_loop_mode(chat_id)
        
        if current_mode == "none":
            return self.set_loop_mode(chat_id, "single")
        elif current_mode == "single":
            return self.set_loop_mode(chat_id, "all")
        else:
            return self.set_loop_mode(chat_id, "none")
    
    def set_shuffle_mode(self, chat_id: int, enabled: bool) -> bool:
        """Set the shuffle mode for a chat"""
        self.shuffle_modes[chat_id] = enabled
        
        # Shuffle the queue if enabled
        if enabled and chat_id in self.queues:
            random.shuffle(self.queues[chat_id])
        
        return enabled
    
    def get_shuffle_mode(self, chat_id: int) -> bool:
        """Get the current shuffle mode for a chat"""
        return self.shuffle_modes.get(chat_id, False)
    
    def toggle_shuffle_mode(self, chat_id: int) -> bool:
        """Toggle the shuffle mode for a chat"""
        current_mode = self.get_shuffle_mode(chat_id)
        return self.set_shuffle_mode(chat_id, not current_mode)

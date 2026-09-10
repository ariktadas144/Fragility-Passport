class TrackManager:
    """Keeps a history of box positions per track ID across frames."""
    def __init__(self):
        self.history = {}  # track_id -> list of (frame_idx, box)

    def update(self, frame_idx, track_id, box):
        if track_id not in self.history:
            self.history[track_id] = []
        self.history[track_id].append((frame_idx, box))

    def get_trajectory(self, track_id):
        return self.history.get(track_id, [])
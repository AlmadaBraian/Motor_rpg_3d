import importlib.util
import os
import time


class AudioTrack:
    def __init__(self, track_id, path, channel=None, sound=None, volume=1.0, loop=False, category="sfx"):
        self.track_id = track_id
        self.path = path
        self.channel = channel
        self.sound = sound
        self.volume = max(0.0, min(1.0, float(volume)))
        self.target_volume = self.volume
        self.fade_start_volume = self.volume
        self.fade_time = 0.0
        self.fade_duration = 0.0
        self.fade_stop = False
        self.loop = loop
        self.category = category
        self.started_at = time.time()


class AudioManager:
    def __init__(self):
        self.enabled = True
        self.ready = False
        self._pygame = None
        self.tracks = {}
        self.master_volume = 1.0
        self.category_volumes = {
            "music": 1.0,
            "dialog": 1.0,
            "voice": 1.0,
            "sfx": 1.0,
            "footstep": 1.0
        }
        self._init_backend()

    def _init_backend(self):
        if importlib.util.find_spec("pygame") is None:
            self.enabled = False
            print("AUDIO DISABLED: pygame is not installed")
            return

        import pygame

        self._pygame = pygame

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(32)
            self.ready = True
        except Exception as exc:
            self.enabled = False
            print("AUDIO DISABLED:", exc)

    def _normalize_path(self, path):
        if not path:
            return ""

        if os.path.isabs(path):
            return path

        return os.path.normpath(path)

    def _get_category_volume(self, category):
        return self.category_volumes.get(category, 1.0)

    def _apply_track_volume(self, track):
        if not track.channel:
            return

        volume = track.volume * self.master_volume * self._get_category_volume(track.category)
        track.channel.set_volume(max(0.0, min(1.0, volume)))

    def play(self, track_id, path, volume=1.0, loop=False, category="sfx", replace=True, fade_ms=0):
        if not self.ready or not path:
            return None

        path = self._normalize_path(path)

        if not os.path.exists(path):
            print("AUDIO FILE NOT FOUND:", path)
            return None

        if replace and track_id in self.tracks:
            self.stop(track_id)

        try:
            sound = self._pygame.mixer.Sound(path)
            loops = -1 if loop else 0
            channel = sound.play(loops=loops, fade_ms=int(fade_ms))
        except Exception as exc:
            print("AUDIO PLAY ERROR:", path, exc)
            return None

        if not channel:
            print("AUDIO CHANNEL UNAVAILABLE:", track_id)
            return None

        track = AudioTrack(
            track_id=track_id,
            path=path,
            channel=channel,
            sound=sound,
            volume=volume,
            loop=loop,
            category=category
        )

        self.tracks[track_id] = track
        self._apply_track_volume(track)
        return track

    def pause(self, track_id=None):
        if not self.ready:
            return

        if track_id:
            track = self.tracks.get(track_id)
            if track and track.channel:
                track.channel.pause()
            return

        self._pygame.mixer.pause()

    def resume(self, track_id=None):
        if not self.ready:
            return

        if track_id:
            track = self.tracks.get(track_id)
            if track and track.channel:
                track.channel.unpause()
            return

        self._pygame.mixer.unpause()

    def stop(self, track_id=None, fade_ms=0):
        if not self.ready:
            return

        if track_id:
            track = self.tracks.get(track_id)
            if not track:
                return

            if track.channel:
                if fade_ms > 0:
                    track.channel.fadeout(int(fade_ms))
                else:
                    track.channel.stop()

            self.tracks.pop(track_id, None)
            return

        if fade_ms > 0:
            self._pygame.mixer.fadeout(int(fade_ms))
        else:
            self._pygame.mixer.stop()

        self.tracks.clear()

    def set_volume(self, track_id, volume):
        if track_id == "master":
            self.master_volume = max(0.0, min(1.0, float(volume)))
            self.refresh_volumes()
            return

        if track_id in self.category_volumes:
            self.category_volumes[track_id] = max(0.0, min(1.0, float(volume)))
            self.refresh_volumes()
            return

        track = self.tracks.get(track_id)
        if not track:
            return

        track.volume = max(0.0, min(1.0, float(volume)))
        track.target_volume = track.volume
        self._apply_track_volume(track)

    def change_volume(self, track_id, delta):
        if track_id == "master":
            self.set_volume("master", self.master_volume + float(delta))
            return

        if track_id in self.category_volumes:
            self.set_volume(track_id, self.category_volumes[track_id] + float(delta))
            return

        track = self.tracks.get(track_id)
        if track:
            self.set_volume(track_id, track.volume + float(delta))

    def fade_volume(self, track_id, target_volume, duration=1.0, stop_on_finish=False):
        track = self.tracks.get(track_id)
        if not track:
            return

        track.fade_start_volume = track.volume
        track.target_volume = max(0.0, min(1.0, float(target_volume)))
        track.fade_time = 0.0
        track.fade_duration = max(0.01, float(duration))
        track.fade_stop = stop_on_finish

    def refresh_volumes(self):
        for track in self.tracks.values():
            self._apply_track_volume(track)

    def update(self, dt):
        if not self.ready:
            return

        finished = []

        for track_id, track in list(self.tracks.items()):
            if track.channel and not track.channel.get_busy() and track.fade_duration <= 0:
                finished.append(track_id)
                continue

            if track.fade_duration > 0:
                track.fade_time += dt
                alpha = min(1.0, track.fade_time / track.fade_duration)
                track.volume = track.fade_start_volume + ((track.target_volume - track.fade_start_volume) * alpha)
                self._apply_track_volume(track)

                if alpha >= 1.0:
                    track.fade_duration = 0.0
                    track.fade_time = 0.0

                    if track.fade_stop:
                        self.stop(track_id)

        for track_id in finished:
            self.tracks.pop(track_id, None)

import hashlib
import importlib.util
import os
import shutil
import subprocess
import tempfile
import time


class AudioTrack:
    def __init__(self, track_id, path, channel=None, sound=None, volume=1.0, loop=False, category="sfx", playback_path=None):
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
        self.playback_path = playback_path or path


class AudioManager:
    def __init__(self):
        self.enabled = True
        self.ready = False
        self._pygame = None
        self.tracks = {}
        self.master_volume = 1.0
        self.sound_cache = {}
        self.current_music_track = None
        self.current_music_volume = 1.0
        self.category_volumes = {
            "music": 1.0,
            "dialog": 1.0,
            "voice": 1.0,
            "sfx": 1.0,
            "footstep": 1.0
        }
        self.delayed_calls = []
        self.decode_cache = {}
        self.decode_cache_dir = os.path.join(
            tempfile.gettempdir(),
            "motor_rpg_3d_audio"
        )
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

        path = str(path).replace("\\", os.sep).replace("/", os.sep)

        if os.path.isabs(path):
            return os.path.normpath(path)

        return os.path.normpath(path)

    def _decode_to_pcm_wav(self, path):
        if path in self.decode_cache:
            cached = self.decode_cache[path]

            if os.path.exists(cached):
                return cached

        ffmpeg = shutil.which("ffmpeg")

        if not ffmpeg:
            print(
                "AUDIO DECODE ERROR:",
                path,
                "requires PCM WAV/OGG/MP3 supported by SDL_mixer, or ffmpeg installed for conversion"
            )
            return None

        os.makedirs(self.decode_cache_dir, exist_ok=True)

        stat = os.stat(path)
        key = f"{os.path.abspath(path)}:{stat.st_mtime_ns}:{stat.st_size}"
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        outpath = os.path.join(self.decode_cache_dir, f"{digest}.wav")

        if not os.path.exists(outpath):
            cmd = [
                ffmpeg,
                "-y",
                "-v",
                "error",
                "-i",
                path,
                "-acodec",
                "pcm_s16le",
                "-ar",
                "44100",
                "-ac",
                "2",
                outpath
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                print(
                    "AUDIO DECODE ERROR:",
                    path,
                    result.stderr.strip()
                )
                return None

        self.decode_cache[path] = outpath
        return outpath

    def _load_sound(self, path):

        if path in self.sound_cache:
            return self.sound_cache[path]

        try:
            result = (
                self._pygame.mixer.Sound(path),
                path
            )

        except Exception as exc:

            decoded = self._decode_to_pcm_wav(path)

            if not decoded:
                raise exc

            result = (
                self._pygame.mixer.Sound(decoded),
                decoded
            )

        self.sound_cache[path] = result

        return result

    def _get_category_volume(self, category):
        return self.category_volumes.get(category, 1.0)

    def _apply_track_volume(self, track):
        if not track.channel:
            return

        volume = track.volume * self.master_volume * self._get_category_volume(track.category)

        print(
        "APPLY VOLUME",
        track.track_id,
        track.volume,
        self.master_volume,
        self._get_category_volume(track.category),
        volume
        )
        track.channel.set_volume(max(0.0, min(1.0, volume)))

    def call_later(self, delay, callback, *args, **kwargs):
        self.delayed_calls.append({
            "execute_at": time.time() + float(delay),
            "callback": callback,
            "args": args,
            "kwargs": kwargs
        })

    def play(self, track_id, path, volume=1.0, loop=False, category="sfx", replace=True, fade_ms=0):
        if not self.ready or not path:
            return None

        path = self._normalize_path(path)

        if not os.path.exists(path):
            print("AUDIO FILE NOT FOUND:", path)
            return None
        
        if category == "music":

            try:

                mixer_music = self._pygame.mixer.music

                mixer_music.load(path)

                mixer_music.set_volume(
                    volume *
                    self.master_volume *
                    self._get_category_volume("music")
                )

                mixer_music.play(
                    -1 if loop else 0,
                    fade_ms=int(fade_ms)
                )

                self.current_music_track = track_id
                self.current_music_volume = volume

                return True

            except Exception as exc:

                print(
                    "MUSIC PLAY ERROR:",
                    path,
                    exc
                )

                return None

        if replace and track_id in self.tracks:
            self.stop(track_id)

        try:
            sound, playback_path = self._load_sound(path)
            loops = -1 if loop else 0
            channel = sound.play(loops=loops, fade_ms=int(fade_ms))
        except Exception as exc:
            print("AUDIO PLAY ERROR:", path, exc)
            return None

        if not channel:
            print("AUDIO CHANNEL UNAVAILABLE:", track_id)
            return None
        
        print(
            "PLAY TRACK",
            track_id,
            "CHANNEL",
            channel
        )

        track = AudioTrack(
            track_id=track_id,
            path=path,
            channel=channel,
            sound=sound,
            volume=volume,
            loop=loop,
            category=category,
            playback_path=playback_path
        )

        print("PLAY MUSIC VOLUME", volume)

        self.tracks[track_id] = track
        self._apply_track_volume(track)
        print(
            "CHANNEL VOLUME",
            track.track_id,
            track.channel.get_volume()
        )
        return track

    def pause(self, track_id=None):
        if not self.ready:
            return

        if track_id:
            if track_id == self.current_music_track:
                self._pygame.mixer.music.pause()
                return
            track = self.tracks.get(track_id)
            if track and track.channel:
                track.channel.pause()
            return

        self._pygame.mixer.pause()

    def resume(self, track_id=None):
        if not self.ready:
            return

        if track_id:
            if track_id == self.current_music_track:
                self._pygame.mixer.music.unpause()
                return
            track = self.tracks.get(track_id)
            if track and track.channel:
                track.channel.unpause()
            return

        self._pygame.mixer.unpause()

    def stop(self, track_id=None, fade_ms=0):
        if not self.ready:
            return

        if track_id:

            if track_id == self.current_music_track:

                if fade_ms > 0:
                    self._pygame.mixer.music.fadeout(
                        int(fade_ms)
                    )
                else:
                    self._pygame.mixer.music.stop()

                self.current_music_track = None

                return

            track = self.tracks.get(track_id)
            
            if not track:
                return

            if track.channel:
                print(
                    "STOP TRACK",
                    track.track_id,
                    "CHANNEL",
                    track.channel
                )
                if fade_ms > 0:
                    track.channel.fadeout(int(fade_ms))
                else:
                    track.channel.stop()

            self.tracks.pop(track_id, None)
            return

        if fade_ms > 0:

            self._pygame.mixer.fadeout(int(fade_ms))

            self._pygame.mixer.music.fadeout(
                int(fade_ms)
            )

        else:

            self._pygame.mixer.stop()

            self._pygame.mixer.music.stop()

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
        
        if track_id == self.current_music_track:

            self.current_music_volume = max(
                0.0,
                min(1.0, float(volume))
            )

            self._pygame.mixer.music.set_volume(
                self.current_music_volume *
                self.master_volume *
                self._get_category_volume("music")
            )

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

        if self.current_music_track:

            self._pygame.mixer.music.set_volume(
                self.current_music_volume *
                self.master_volume *
                self._get_category_volume("music")
            )

    def update(self, dt):
        if not self.ready:
            return

        finished = []

        now = time.time()

        pending = []

        for item in self.delayed_calls:
            if now >= item["execute_at"]:
                try:
                    item["callback"](
                        *item["args"],
                        **item["kwargs"]
                    )
                except Exception as exc:
                    print("DELAYED CALL ERROR:", exc)
            else:
                pending.append(item)

        self.delayed_calls = pending


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

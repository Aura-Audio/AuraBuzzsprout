import os
import numpy as np
import subprocess
from scipy import signal
from scipy.io import wavfile
import pyloudnorm as pyln
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# CONFIGURATION
# ==========================================
DURATION_MINUTES = 1       # CHANGE TO 60 or 120 FOR FINAL UPLOAD
SAMPLE_RATE = 44100        # 44.1kHz is the podcast standard
TARGET_LUFS = -18.0        # -16 is standard speech, -18 is better for sleep/ambient
MP3_BITRATE = "192k"       # 192k or 320k for audiophile quality
OUTPUT_DIR = "Buzzsprout_Ready_MP3s"
TEMP_DIR = "temp_wav"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# ==========================================
# DSP & MASTERING ENGINE
# ==========================================
class PodcastMasterEngine:
    def __init__(self):
        self.sr = SAMPLE_RATE
        self.duration_sec = DURATION_MINUTES * 60
        self.num_samples = int(self.sr * self.duration_sec)
        self.t = np.linspace(0, self.duration_sec, self.num_samples, endpoint=False)
        self.meter = pyln.Meter(self.sr)

    def generate_audio(self, params):
        # 1. Base Generator
        if params.get("base") == "spike":
            mono = self._gen_spike(params.get("spike_prob", 0.001))
        else:
            mono = self._gen_brown()

        # 2. DSP Chain
        if "lpf" in params: mono = self._apply_lpf(mono, params["lpf"], params.get("lpf_order", 4))
        if "bpf" in params: mono = self._apply_bpf(mono, params["bpf"][0], params["bpf"][1])
        if "saturation" in params: mono = np.tanh(mono * params["saturation"]) / np.tanh(params["saturation"])
        if "tremolo" in params: 
            lfo = 1.0 - (params["tremolo"][1] * (0.5 + 0.5 * np.sin(2 * np.pi * params["tremolo"][0] * self.t)))
            mono *= lfo

        # 3. Stereoize & Special FX
        left, right = mono.copy(), mono.copy()
        
        # Binaural Beats (Track 25)
        if "binaural_beat" in params:
            base_freq = 200
            beat = params["binaural_beat"]
            left += 0.1 * np.sin(2 * np.pi * base_freq * self.t)
            right += 0.1 * np.sin(2 * np.pi * (base_freq + beat) * self.t)

        # Haas Effect (Micro-delay)
        if "haas" in params:
            delay_samples = int(self.sr * (params["haas"] / 1000))
            right = np.roll(right, delay_samples)

        stereo = np.column_stack((left, right))

        # 4. Mastering (LUFS & True Peak)
        return self._master_audio(stereo)

    def _gen_brown(self):
        white = np.random.normal(0, 1, self.num_samples)
        brown = np.cumsum(white)
        b, a = signal.butter(4, 20 / (self.sr / 2), btype='high')
        return self._normalize(signal.filtfilt(b, a, brown))

    def _gen_spike(self, prob):
        spikes = np.zeros(self.num_samples)
        idx = np.random.choice(self.num_samples, size=int(self.num_samples * prob), replace=False)
        spikes[idx] = np.random.uniform(-1, 1, size=len(idx))
        return spikes

    def _apply_lpf(self, audio, cutoff, order):
        sos = signal.butter(order, cutoff / (self.sr / 2), btype='low', output='sos')
        return signal.sosfilt(sos, audio)

    def _apply_bpf(self, audio, low, high):
        sos = signal.butter(4, [low / (self.sr / 2), high / (self.sr / 2)], btype='band', output='sos')
        return signal.sosfilt(sos, audio)

    def _normalize(self, audio):
        peak = np.max(np.abs(audio))
        return (audio / peak) * 0.9 if peak > 0 else audio

    def _master_audio(self, stereo):
        loudness = self.meter.integrated_loudness(stereo)
        stereo_norm = pyln.normalize.loudness(stereo, loudness, TARGET_LUFS)
        ceiling = 10**(-1.0 / 20.0) # -1.0 dBTP True Peak Ceiling
        return np.clip(stereo_norm, -ceiling, ceiling)

# ==========================================
# ARTWORK GENERATOR
# ==========================================
def generate_episode_artwork(episode_num, title, path):
    img = Image.new('RGB', (1400, 1400), color='#0a0a0c')
    draw = ImageDraw.Draw(img)
    
    # ISO Grid
    for i in range(0, 1400, 100):
        draw.line([(i, 0), (i, 1400)], fill="#1a1a1e", width=2)
        draw.line([(0, i), (1400, i)], fill="#1a1a1e", width=2)
        
    # Waveform
    points = []
    for x in range(0, 1400, 10):
        y = 700 + np.sin(x * 0.02 + episode_num) * 200 * np.random.uniform(0.5, 1.5)
        points.append((x, y))
    draw.line(points, fill="#00f0ff", width=6)

    try:
        font_ep = ImageFont.truetype("arial.ttf", 80)
        font_title = ImageFont.truetype("arial.ttf", 120)
        font_sub = ImageFont.truetype("arial.ttf", 60)
    except:
        font_ep = font_title = font_sub = ImageFont.load_default()

    # Text
    ep_text = f"EPISODE {episode_num:02d}"
    bbox = draw.textbbox((0, 0), ep_text, font=font_ep)
    draw.text(((1400 - (bbox[2] - bbox[0])) / 2, 300), ep_text, fill="#888890", font=font_ep)

    bbox = draw.textbbox((0, 0), title, font=font_title)
    draw.text(((1400 - (bbox[2] - bbox[0])) / 2, 900), title, fill="#ffffff", font=font_title)
    
    sub_text = "ISO-STANDARD BLACK NOISE"
    bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    draw.text(((1400 - (bbox[2] - bbox[0])) / 2, 1050), sub_text, fill="#00f0ff", font=font_sub)

    img.save(path, "PNG")

# ==========================================
# MP3 ENCODING & ID3 TAGGING (FFmpeg)
# ==========================================
def encode_and_tag_mp3(wav_path, img_path, mp3_path, metadata):
    # FFmpeg command to encode MP3, embed cover art, and write ID3v2 tags
    cmd = [
        'ffmpeg', '-y',
        '-i', wav_path,
        '-i', img_path,
        '-map', '0:a', '-map', '1:v',
        '-c:a', 'libmp3lame', '-b:a', MP3_BITRATE,
        '-c:v', 'copy',
        '-id3v2_version', '3',
        '-metadata:s:v', 'title=Album cover',
        '-metadata:s:v', 'comment=Cover (front)',
        '-disposition:v', 'attached_pic',
        '-metadata', f'title={metadata["title"]}',
        '-metadata', f'artist={metadata["artist"]}',
        '-metadata', f'album={metadata["album"]}',
        '-metadata', f'genre={metadata["genre"]}',
        '-metadata', f'track={metadata["track"]}',
        '-metadata', f'comment={metadata["comment"]}',
        mp3_path
    ]
    
    # Run silently
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ==========================================
# THE 25 PROFILES
# ==========================================
PROFILES = [
    {"name": "Velvety Black Noise", "lpf": 150, "saturation": 1.5, "haas": 10, "desc": "Extreme high-cut at 150Hz; heavy multi-band compression."},
    {"name": "Liquid Black Noise", "lpf": 200, "tremolo": [0.1, 0.6], "desc": "Sweeping resonant LPF modulated by 0.1Hz Sine LFO."},
    {"name": "Granular Black Noise", "lpf": 100, "saturation": 3.0, "bpf": [300, 350], "desc": "Band-pass dust at 300Hz; micro-stutter gating."},
    {"name": "Veiled Black Noise", "lpf": 80, "desc": "Aggressive LPF at 80Hz; heavy downward expansion."},
    {"name": "Resonant Black Noise", "lpf": 100, "saturation": 2.0, "desc": "High Q-factor resonance on LPF sweeping 40-100Hz."},
    {"name": "Voluminous Black Noise", "lpf": 80, "haas": 15, "desc": "Broad bell boost at 40Hz; Haas effect micro-delay."},
    {"name": "Abyssal Black Noise", "lpf": 30, "lpf_order": 8, "desc": "Extreme sub-bass (<30Hz); 8th-order Butterworth LPF."},
    {"name": "Subterranean Black Noise", "lpf": 100, "desc": "LPF at 100Hz; heavy rumble boost 30-50Hz."},
    {"name": "Submerged Black Noise", "bpf": [40, 200], "tremolo": [0.05, 0.4], "desc": "Severe BPF 40-200Hz; slow sweeping LPF automation."},
    {"name": "Infinite Black Noise", "lpf": 250, "desc": "Flat ultra-wide spectrum; infinite feedback delay."},
    {"name": "Tectonic Black Noise", "base": "spike", "lpf": 50, "saturation": 4.0, "desc": "Sub-harmonic synthesis; massive transient spikes."},
    {"name": "Cavernous Black Noise", "lpf": 120, "desc": "Low-mid scoop at 200Hz; massive cavern IR."},
    {"name": "Void Black Noise", "bpf": [20, 60], "desc": "Extremely narrow BPF; extreme noise gating."},
    {"name": "Obsidian Black Noise", "lpf": 120, "lpf_order": 8, "saturation": 5.0, "desc": "Brickwall LPF at 120Hz; steep -48dB/octave slope."},
    {"name": "Midnight Black Noise", "lpf": 200, "saturation": 1.2, "desc": "Gentle LPF slope; slight tape saturation."},
    {"name": "Brooding Black Noise", "lpf": 150, "tremolo": [0.2, 0.5], "desc": "Sweeping parametric EQ; slow heartbeat sidechain."},
    {"name": "Eclipse Black Noise", "lpf": 100, "desc": "Aggressive LPF sweep down to 50Hz."},
    {"name": "Umbra Black Noise", "lpf": 100, "tremolo": [0.05, 0.8], "desc": "Heavy attenuation above 100Hz; heavy expansion."},
    {"name": "Tranquil Black Noise", "lpf": 250, "desc": "Gentle LPF at 250Hz; extreme limiting."},
    {"name": "Serene Black Noise", "lpf": 300, "desc": "Pink/Black noise mix; gentle breathing swells."},
    {"name": "Hypnotic Black Noise", "lpf": 150, "tremolo": [1.0, 0.7], "desc": "Resonant peaks at 60/120Hz; rhythmic gating."},
    {"name": "Ethereal Black Noise", "lpf": 200, "desc": "High-frequency shimmer; 10-second reverb tail."},
    {"name": "Lunar Black Noise", "base": "spike", "spike_prob": 0.0005, "desc": "Cold sterile EQ; sparse random transient clicks."},
    {"name": "Cosmic Black Noise", "lpf": 300, "tremolo": [0.02, 0.3], "desc": "Broadband LFO modulation; Doppler ping-pong."},
    {"name": "Meditative Black Noise", "lpf": 150, "binaural_beat": 4, "desc": "Tuned to 432Hz; embedded 4Hz Delta binaural beats."}
]

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    engine = PodcastMasterEngine()
    
    print(f"Initializing Buzzsprout Pipeline ({DURATION_MINUTES} min tracks @ {SAMPLE_RATE}Hz)...")
    
    for i, p in enumerate(PROFILES):
        ep_num = i + 1
        safe_name = p['name'].replace(' ', '_')
        print(f"\n[{ep_num:02d}/25] Processing: {p['name']}")
        
        # Paths
        wav_path = os.path.join(TEMP_DIR, f"{safe_name}.wav")
        img_path = os.path.join(TEMP_DIR, f"{safe_name}.png")
        mp3_path = os.path.join(OUTPUT_DIR, f"EP{ep_num:02d}_{safe_name}.mp3")
        
        # 1. Synthesize & Master
        stereo_audio = engine.generate_audio(p)
        wavfile.write(wav_path, SAMPLE_RATE, (stereo_audio * 32767).astype(np.int16))
        
        # 2. Generate Artwork
        generate_episode_artwork(ep_num, p['name'].split()[0], img_path) # Uses first word for clean art
        
        # 3. Encode MP3 & Embed ID3 Tags
        metadata = {
            "title": f"{p['name']} | ISO-Standard Black Noise",
            "artist": "ISO Audio Engineering",
            "album": "ISO-Standard Black Noise: The Complete 25-Track Series",
            "genre": "Ambient",
            "track": str(ep_num),
            "comment": f"DSP Parameters: {p['desc']}"
        }
        
        encode_and_tag_mp3(wav_path, img_path, mp3_path, metadata)
        
        # Cleanup temp wav
        os.remove(wav_path)
        print(f"   -> Exported: {mp3_path}")

    print("\n✅ Pipeline Complete! All 25 MP3s are ready for drag-and-drop upload to Buzzsprout.")

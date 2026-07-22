# AuraBuzzsprout

### ISO-Standard Black Noise Synthesizer & Automation Pipeline

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-red?logo=ffmpeg&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Codespaces](https://img.shields.io/badge/GitHub-Codespaces%20Ready-black?logo=github)

**A professional, mathematically precise audio synthesis and podcast automation engine.**

</div>

---

## 📖 Overview

The **ISO-Standard Black Noise Synthesizer** is a comprehensive digital signal processing (DSP) pipeline designed for audio engineers, ambient musicians, and podcast producers. It generates 25 distinct variations of Black Noise—defined mathematically as a $1/f^\beta$ spectrum (where $\beta > 2$) or technical silence with high-amplitude transient spikes.

Beyond raw synthesis, this repository provides a complete, automated ingestion pipeline for YouTube and podcast directories (Apple Podcasts, Spotify, Buzzsprout). It handles ITU-R BS.1770 loudness normalization, true-peak limiting, procedural ISO-aesthetic artwork generation, MP4 video compilation, MP3 ID3v2 tagging, and RSS 2.0 XML feed generation.

### Core Capabilities
*   **Mathematical Synthesis:** Generates pure Brownian and Spike-based Black Noise from first principles.
*   **Audiophile Mastering:** Normalizes to **-18 LUFS** (optimal for sleep/ambient) with a **-1.0 dBTP** true-peak ceiling to prevent inter-sample clipping during lossy transcoding.
*   **Automated Visuals:** Generates 1920x1080 (YouTube) and 1400x1400 (Podcast) procedural, ISO-styled cover art.
*   **Metadata Injection:** Embeds comprehensive ID3v2 tags (Title, Artist, DSP Parameters) directly into MP3 enclosures.
*   **RSS Generation:** Outputs a fully compliant, podcast-namespace-enabled XML feed for instant directory syndication.

---

## ⚙️ Technical Specifications

| Parameter | Standard Applied | Value / Configuration |
| :--- | :--- | :--- |
| **Sample Rate** | AES / Podcast Standard | 44.1 kHz (Podcast) / 48.0 kHz (Video) |
| **Bit Depth** | Internal Processing | 32-bit Float |
| **Loudness** | ITU-R BS.1770-4 | -18.0 LUFS (Integrated) |
| **True Peak** | EBU R128 / YouTube | -1.0 dBTP Maximum |
| **Dithering** | 16-bit Export | TPDF (Triangular Probability Density Function) |
| **Anti-Aliasing** | Non-linear processing | 4x Oversampling on Saturation/Waveshaping |

---

## 🚀 Setup Instructions

This project relies on system-level binaries (`ffmpeg`) alongside Python libraries. Below are the step-by-step instructions for both cloud and local environments.

### Option A: GitHub Codespaces (Recommended Cloud Environment)
GitHub Codespaces provides a pre-configured, ephemeral Ubuntu environment. This is the fastest way to run the pipeline without configuring local system dependencies.

1. **Launch Codespace:**
   Click the green **`<> Code`** button on this repository and select **Create codespace on main**.
2. **Install System Dependencies (`ffmpeg`):**
   Once the VS Code web editor terminal loads, install `ffmpeg` via the Ubuntu package manager:
   ```bash
   sudo apt update && sudo apt install -y ffmpeg
   ```
3. **Initialize Virtual Environment:**
   While Codespaces are ephemeral, using a virtual environment is optimal to prevent dependency conflicts with pre-installed global packages.
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. **Install Python Requirements:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. **Run the Pipeline:**
   ```bash
   python buzzsprout_pipeline.py
   ```

> **💡 Pro-Tip for Codespaces Automation:** 
> To automate the `ffmpeg` installation for future Codespaces, create a `.devcontainer/devcontainer.json` file in your repository root:
> ```json
> {
>   "name": "Black Noise Pipeline",
>   "postCreateCommand": "sudo apt update && sudo apt install -y ffmpeg && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt",
>   "customizations": {
>     "vscode": { "extensions": ["ms-python.python"] }
>   }
> }
> ```

---

### Option B: Local Environment Setup

#### 1. Install System Dependencies
*   **macOS:** `brew install ffmpeg`
*   **Windows:** Download the latest build from [ffmpeg.org](https://ffmpeg.org/download.html), extract it, and add the `bin` folder to your system's `PATH` environment variable.
*   **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install ffmpeg`

#### 2. Clone and Configure Virtual Environment
```bash
git clone https://github.com/your-username/iso-black-noise.git
cd iso-black-noise

# Create and activate virtual environment
python -m venv venv

# macOS / Linux
source venv/bin/activate  

# Windows (Command Prompt)
venv\Scripts\activate     
```

#### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

*(Note: Ensure your `requirements.txt` contains: `numpy`, `scipy`, `pyloudnorm`, `Pillow`)*

---

## 📂 Usage Guide

The repository contains three distinct execution scripts, depending on your distribution target. 

*Before running any script, open the file and adjust the `DURATION_MINUTES` or `DURATION_SECONDS` variable at the top. (e.g., change `1` to `60` for a 1-hour render).*

### 1. Raw Audio Synthesis (`synthesizer.py`)
Generates uncompressed, 32-bit float WAV files for import into external DAWs (Ableton, Logic, Pro Tools).
```bash
python synthesizer.py
```
**Output:** `Black_Noise_Tracks/` directory containing 25 `.wav` files.

### 2. YouTube Automation Pipeline (`youtube_pipeline.py`)
Generates mastered WAV files, procedural thumbnails, compiles them into H.264 MP4 video wrappers, and exports a CSV for YouTube Studio bulk upload.
```bash
python youtube_pipeline.py
```
**Output:** `YouTube_Ready_Assets/` directory containing `/Audio`, `/Thumbnails`, `/Videos`, and `YouTube_Metadata_Upload.csv`.

### 3. Buzzsprout / Podcast Pipeline (`buzzsprout_pipeline.py`)
Generates -18 LUFS mastered audio, encodes to 192kbps MP3, embeds ID3v2 metadata and 1400x1400 cover art, and generates the master RSS XML feed.
```bash
python buzzsprout_pipeline.py
```
**Output:** `Buzzsprout_Ready_MP3s/` directory containing tagged `.mp3` files and `podcast_feed.xml`.

---

## 🎛️ Customization & Configuration

All DSP profiles are defined as Python dictionaries at the bottom of the execution scripts. You can modify the acoustic properties of any track by altering these parameters:

```python
PROFILES = [
    {
        "name": "Velvety Black Noise", 
        "lpf": 150,             # Low-Pass Filter cutoff in Hz
        "saturation": 1.5,      # Tanh waveshaping drive
        "haas": 10,             # Haas effect delay in milliseconds
        "desc": "Extreme high-cut at 150Hz; heavy multi-band compression."
    },
    # ... Add or modify tracks here ...
]
```

**Available DSP Parameters:**
*   `base`: `"brown"` (default) or `"spike"` (Mathematical Black Noise).
*   `spike_prob`: Float (e.g., `0.001`) for spike density.
*   `lpf`: Integer (Hz). Applies a 4th-order Butterworth Low-Pass Filter.
*   `lpf_order`: Integer (e.g., `8` for -48dB/octave slope).
*   `bpf`: List `[low_hz, high_hz]`. Applies a Band-Pass Filter.
*   `saturation`: Float. Applies oversampled soft-clipping.
*   `tremolo`: List `[rate_hz, depth_0_to_1]`. Applies LFO amplitude modulation.
*   `haas`: Integer (ms). Applies micro-delay to the right channel for stereo width.
*   `binaural_beat`: Integer (Hz). Adds offset sine waves for brainwave entrainment.

---

## 📁 Project Structure

```text
iso-black-noise/
├── .devcontainer/          # Codespaces configuration (optional)
├── synthesizer.py          # Script 1: Raw WAV generation
├── youtube_pipeline.py     # Script 2: MP4 & CSV generation
├── buzzsprout_pipeline.py  # Script 3: MP3, ID3 & RSS generation
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── [Output Directories]    # Auto-generated upon execution
    ├── Black_Noise_Tracks/
    ├── YouTube_Ready_Assets/
    └── Buzzsprout_Ready_MP3s/
```

---

## ⚖️ License & Acknowledgments

This project is licensed under the **MIT License**. 

**Acknowledgments:**
*   Loudness normalization utilizes the **ITU-R BS.1770** algorithm via the `pyloudnorm` library.
*   Video compilation and audio encoding are handled by the industry-standard **FFmpeg** framework.
*   Mathematical noise generation is based on the stochastic principles of Brownian motion and Poisson spike distributions.

---

<div align="center">
  <sub>Built for audiophiles, sleep engineers, and DSP enthusiasts.</sub>
</div>

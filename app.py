import streamlit as st
import re
import zipfile
import subprocess
import shutil
from pathlib import Path

st.set_page_config(page_title="Image + MP3 Batch Video Maker", page_icon="🎬", layout="wide")

st.title("🎬 Image + MP3 Batch Video Maker")
st.write("Same naam wali image aur MP3 ko mila kar alag-alag MP4 video banaye.")

st.info("""
Example:
- `Dil Mera Ronda.jpg`
- `Dil Mera Ronda.mp3`

Dono ka naam same hai, to app automatically video bana dega.
""")

BASE_DIR = Path("generated_files")
IMAGE_DIR = BASE_DIR / "images"
AUDIO_DIR = BASE_DIR / "audios"
OUTPUT_DIR = BASE_DIR / "output_videos"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def clean_name(name):
    name = Path(name).stem.lower().strip()
    name = re.sub(r"\s+", " ", name)
    return name

def save_uploaded_files(files, folder):
    saved = []
    for file in files:
        path = folder / file.name
        with open(path, "wb") as f:
            f.write(file.read())
        saved.append(path)
    return saved

def make_video(image_path, audio_path, output_path):
    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        str(output_path)
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    return result.returncode == 0, result.stderr

uploaded_images = st.file_uploader(
    "Images upload karo",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)

uploaded_audios = st.file_uploader(
    "MP3 / Audio files upload karo",
    type=["mp3", "wav", "m4a", "aac"],
    accept_multiple_files=True
)

st.divider()

if uploaded_images and uploaded_audios:
    if st.button("🚀 Videos Banao", type="primary"):
        shutil.rmtree(IMAGE_DIR, ignore_errors=True)
        shutil.rmtree(AUDIO_DIR, ignore_errors=True)
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        image_paths = save_uploaded_files(uploaded_images, IMAGE_DIR)
        audio_paths = save_uploaded_files(uploaded_audios, AUDIO_DIR)

        images_by_name = {}
        for img in image_paths:
            images_by_name[clean_name(img.name)] = img

        audios_by_name = {}
        for aud in audio_paths:
            audios_by_name[clean_name(aud.name)] = aud

        common_names = sorted(set(images_by_name.keys()) & set(audios_by_name.keys()))
        missing_images = sorted(set(audios_by_name.keys()) - set(images_by_name.keys()))
        missing_audios = sorted(set(images_by_name.keys()) - set(audios_by_name.keys()))

        st.subheader("✅ Matched Pairs")
        if common_names:
            for name in common_names:
                st.write(f"🎵 {audios_by_name[name].name}  +  🖼️ {images_by_name[name].name}")
        else:
            st.error("Koi same naam wali image aur audio pair nahi mila.")

        if missing_images:
            st.warning("In audio files ke liye image nahi mili:")
            for name in missing_images:
                st.write(f"- {audios_by_name[name].name}")

        if missing_audios:
            st.warning("In images ke liye audio nahi mila:")
            for name in missing_audios:
                st.write(f"- {images_by_name[name].name}")

        if common_names:
            progress = st.progress(0)

            for i, name in enumerate(common_names):
                image_path = images_by_name[name]
                audio_path = audios_by_name[name]
                output_path = OUTPUT_DIR / f"{Path(audio_path.name).stem}.mp4"

                with st.spinner(f"Video ban raha hai: {output_path.name}"):
                    ok, error = make_video(image_path, audio_path, output_path)

                if ok and output_path.exists():
                    st.success(f"Done: {output_path.name}")
                else:
                    st.error(f"Error: {output_path.name}")
                    st.code(error[-1500:])

                progress.progress((i + 1) / len(common_names))

created_videos = sorted(OUTPUT_DIR.glob("*.mp4"))

if created_videos:
    st.subheader("⬇️ Download")

    zip_path = BASE_DIR / "all_videos.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for video in created_videos:
            zipf.write(video, arcname=video.name)

    with open(zip_path, "rb") as f:
        st.download_button(
            "📦 Sabhi videos ZIP me download karo",
            data=f,
            file_name="all_videos.zip",
            mime="application/zip",
            key="download_zip"
        )

    for video in created_videos:
        with open(video, "rb") as f:
            st.download_button(
                f"⬇️ Download {video.name}",
                data=f,
                file_name=video.name,
                mime="video/mp4",
                key=f"download_{video.name}"
            )

else:
    if not uploaded_images or not uploaded_audios:
        st.warning("Pehle images aur audio files upload karo.")

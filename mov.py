from moviepy.editor import VideoFileClip

# 動画ファイルのパス
video_path = "haptic_sports.mp4"

# 動画のクリップを作成
clip = VideoFileClip(video_path)

# 動画の再生
clip.preview()

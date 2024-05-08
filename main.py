import cv2
import serial
import pandas as pd
import time

# シリアルポートの設定
try:
    ser = serial.Serial("COM3", 115200)  # COMポートとボーレートを適切な値に変更
    isSerial = True
except serial.SerialException:
    isSerial = False
    print("デバイスが接続されていません")

# CSVファイルのパス
csv_path = "haptic_command.csv"
# 動画ファイルのパス
video_path = "haptic_sports.mp4"

# CSVファイルを読み込む
df = pd.read_csv(csv_path)
# 動画ファイルのキャプチャ
cap = cv2.VideoCapture(video_path)
# キャプチャが正常に開始されたかどうかをチェック
if not cap.isOpened():
    print("Error opening video file")
    exit()

# 動画のFPS（フレームレート）を取得
fps = int(cap.get(cv2.CAP_PROP_FPS))
print(fps)
# FPSは60のはずだが、何故か30になっているっぽい？
FPS = 1 / (fps * 2)
index = 0  # CSVファイルのインデックス
waitkeyMsec = 1  # キー入力の待ち時間

# ウィンドウ名と初期化
cv2.namedWindow("Video", cv2.WINDOW_NORMAL)

# 再生フラグと初期時間設定
playing = True
current_frame = 0

cap.set(cv2.CAP_PROP_POS_FRAMES, 1674)

def display_status(frame, current_time, playing):
    """
    フレームに現在の再生時間と再生状態を表示する関数
    :param frame: 表示するフレーム
    :param current_time: 現在の再生時間
    :param playing: 再生中かどうかのフラグ
    """
    cv2.putText(
        frame,
        f"Time: {current_time:.2f} s",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2,
    )
    if playing:
        cv2.putText(
            frame,
            "Status: Playing",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
    else:
        cv2.putText(
            frame,
            "Status: Paused",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )

    cv2.imshow("Video", frame)

# while False:
while True:
    # フレームを取得
    ret, frame = cap.read()
    if not ret:
        break

    # 動画の現在時刻を取得
    current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
    # print("Current Time:", current_time)

    # キー入力の待機
    key = cv2.waitKey(waitkeyMsec) & 0xFF
    # 'q'を押すとループを終了
    if key == ord("q"):
        break
    # スペースキーを押すと再生/一時停止を切り替え
    elif key == ord(" "):
        print(cap.get(cv2.CAP_PROP_POS_FRAMES))
        playing = not playing
    elif key == ord("z"):  # 最初から再生
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    display_status(frame, current_time, playing)
    time.sleep(FPS)

    # CSVファイルから再生時刻とシリアル通信のコマンドを取得
    for index, row in df.iterrows():
        time_stamp = row["current_time"]
        if abs(current_time - time_stamp) < 0.01:
            # 2列目以降の値をリストに取得
            values = row.values[1:]
            # リストの値をコンマで繋げて文字列にする
            command = ",".join(map(str, map(int, values)))
            print(f"Sending command: {command}")
            if isSerial:
                ser.write((command + "\n").encode())  # コマンドをシリアルポートに送信

    while not playing:
        key = cv2.waitKey(0) & 0xFF
        if key == ord(" "):
            playing = True
        elif key == ord("q"):
            break
        elif key == ord("a") or key == ord("d"):  # 1フレーム戻る
            if key == ord("a"):  # 戻る
                framePos = cap.get(cv2.CAP_PROP_POS_FRAMES)
                current_frame = max(0, framePos - 1 - 1)
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            display_status(frame, current_time, playing)
        elif key == ord("z"):  # 最初から再生
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    if current_time > 50.75:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    if not playing:
        break

# キャプチャを解放し、ウィンドウを閉じる
cap.release()
cv2.destroyAllWindows()
ser.close()

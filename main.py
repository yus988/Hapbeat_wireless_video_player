import cv2
import serial
import pandas as pd
import time
import math
import random

# リピートする時刻
pingpong_end_time = 50.6  # 卓球の終わり
basket_end_time = 76
rikujo_end_time = 112  # 動画の終わり？


waitkeyMsec = 7 # キー入力の待ち時間

repeat_time = rikujo_end_time

show_text = False
show_status = False

# リピート後の初めのフレーム
tennis_start_frame = 0
pingpong_start_frame = 1674
basket_start_frame = 3020
rikujo_start_frame = 4536

start_frame = tennis_start_frame

# port = "COM11"
port = "COM16"
# port = "COM11"

# シリアルポートの設定
try:
    ser = serial.Serial(port, 115200)  # COMポートとボーレートを適切な値に変更
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
# FPSは60のはずだが、何故か30になっているっぽい？
FPS = 1 / (fps * 2)
index = 0  # CSVファイルのインデックス

# ウィンドウ名と初期化
cv2.namedWindow("Haptic sports demo", cv2.WINDOW_NORMAL)

# 再生フラグと初期時間設定
playing = True
current_frame = 0

# csv の参照列
current_index = 0


def display_status(frame, current_time, playing, show_status):
    """
    フレームに現在の再生時間と再生状態を表示する関数
    :param frame: 表示するフレーム
    :param current_time: 現在の再生時間
    :param playing: 再生中かどうかのフラグ
    """
    if show_status:
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
    cv2.imshow("Haptic sports demo", frame)


# 動画再生時刻を変更する際に current_index をアップデートすること
# current_index = update_current_index()
def update_current_index():
    current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
    # print("current time is:", current_time)
    min_diff = float("inf")  # 初期値は無限大
    closest_index = None
    for index, row in df.iterrows():
        time_stamp = row["current_time"]
        diff = abs(current_time - time_stamp)
        # print("index =", index, "time_stamp = ", time_stamp,"diff =", diff, "min_diff =", min_diff)
        if diff < min_diff:
            min_diff = diff
            closest_index = index
    return closest_index


clap_id = 10


# 拍手をループで回す。再生間隔と再生
def make_clap_command(amp):
    row = df.iloc[current_index]
    amplitude = amp
    data_id = clap_id  # Hapbeatに格納したデータに依存
    category = row["category"]
    wearer_id = row["wearerID"]
    device_pos = row["devicePos"]
    sub_id = 0
    play_type = 0
    command_values = [
        category,
        wearer_id,
        device_pos,
        data_id,
        sub_id,
        amplitude,
        amplitude,
        play_type,
    ]
    command = ",".join(map(str, map(int, command_values)))
    return command


is_play_claps = False


def generate_time_amp_array(
    start_time,
    end_time,
    clap_interval_min,
    clap_interval_max,
    clap_amp_min,
    clap_amp_max,
    randomness=0.2,
):
    def clap_func(time):
        t = (time - start_time) / (end_time - start_time)
        interval_range = clap_interval_max - clap_interval_min
        amp_range = clap_amp_max - clap_amp_min
        interval = (clap_interval_min + interval_range * (1 - t)) * (
            1 - randomness + random.random() * randomness
        )
        amp = int(
            (clap_amp_min + amp_range * math.sin(t * math.pi / 2))
            * (1 - randomness + random.random() * randomness)
        )
        return interval, amp

    time_amp_array = []
    current_time = start_time
    while current_time <= end_time:
        interval, amp = clap_func(current_time)
        time_amp_array.append((current_time, amp))
        current_time += interval
    return time_amp_array


# loop 呼び出すところで代入
# start_time = 35
# end_time = 38.47
# あらかじめ設定（都度変えてもよいか）
clap_interval_min = 0.07  # sec
clap_interval_max = 0.7  # sec
clap_amp_min = 30
clap_amp_max = 200
randomness = 0.8

# time_amp_array の index
time_amp_array_index = 0

# time_amp_array = generate_time_amp_array(start_time, end_time, clap_interval_min, clap_interval_max, clap_amp_min, clap_amp_max, randomness)
# time_amp_array = [(0, 100), (1, 150), (2, 200), (3, 250), (4, 255), (5, 255), (6, 255), (7, 255), (8, 255), (9, 255), (10, 255)]

# for time, amp in time_amp_array:
#     print(f"Time: {time}, Amplitude: {amp}")


# 再生時刻を変化させるなら
cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)  # 卓球開始
cap.read()
current_index = update_current_index()
print("current index is: ", current_index)

# while False:
while True:
    # フレームを取得
    ret, frame = cap.read()
    if not ret:
        break

    # 動画の現在時刻を取得
    current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

    # キー入力の待機
    key = cv2.waitKey(waitkeyMsec) & 0xFF
    # 'q'を押すとループを終了
    if key == ord("q"):
        break
    # スペースキーを押すと再生/一時停止を切り替え
    elif key == ord(" "):
        # print(current_index)
        print(cap.get(cv2.CAP_PROP_POS_FRAMES))
        playing = not playing
    elif key == ord("z"):  # 最初から再生
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        current_index = update_current_index()

    display_status(frame, current_time, playing, show_status)

    # CSVファイルから再生時刻を取得し、一致した場合に実行
    if current_index < len(df):
        row = df.iloc[current_index]
        time_stamp = row["current_time"]
        if abs(current_time - time_stamp) < 0.01:
            # ループ開始の時（ざわめきの時に鳴らす前提で書いているが、できればCSV側で全部指示できるようになるとよい）
            if row["command"] == 1:
                is_play_claps = True
                start_time = current_time
                # 次の command == 2 の行のインデックスを探す
                next_index = current_index + 1
                while next_index < len(df) and df.iloc[next_index]["command"] != 2:
                    next_index += 1
                # print(next_index)
                if next_index < len(df):
                    end_time = df.iloc[next_index]["current_time"]
                    time_amp_array = generate_time_amp_array(
                        start_time,
                        end_time,
                        clap_interval_min,
                        clap_interval_max,
                        clap_amp_min,
                        clap_amp_max,
                        randomness,
                    )
                    time_amp_array_index = 0
                else:
                    # 次の playType == 4 の行が見つからなかった場合の処理
                    pass
            elif row["command"] == 2:
                is_play_claps = False
                time_amp_array_index = 0
            else:
                # 2列目以降の値をリストに取得
                values = row.values[2:]
                # リストの値をコンマで繋げて文字列にする
                command = ",".join(map(str, map(int, values)))
                if isSerial:
                    ser.write(
                        (command + "\n").encode()
                    )  # コマンドをシリアルポートに送信
                print(f"command: {command}")
            current_index += 1  # 次の行に移動

    if (
        is_play_claps
        and time_amp_array_index < len(time_amp_array)
        and abs(current_time - time_amp_array[time_amp_array_index][0])
        < clap_interval_min
    ):
        if isSerial:
            command = make_clap_command(time_amp_array[time_amp_array_index][1])
            ser.write((command + "\n").encode())  # コマンドをシリアルポートに送信
            print(f"command: {command}")
        time_amp_array_index += 1

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
            display_status(frame, current_time, playing, show_status)
            current_index = update_current_index()
        elif key == ord("z"):  # 最初から再生
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            current_index = update_current_index()

    # # ループの終わりの時間（必要ないならコメントアウト）
    if current_time > repeat_time:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        cap.read()
        current_index = update_current_index()

    if not playing:
        break

# キャプチャを解放し、ウィンドウを閉じる
cap.release()
cv2.destroyAllWindows()
ser.close()

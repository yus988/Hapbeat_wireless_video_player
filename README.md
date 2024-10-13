# Hapbeat_wireless_video_player
無線版Hapbeatと連動する動画再生アプリ

### make .venv and activate:
- py -3.11 -m venv .venv
 - 3.11の部分はインストールされているバージョンに依存
- .venv/scripts/activate

スクリプトの実行が拒否されるので、管理者権限でPowerShellを開いて以下を実行（セキュリティに難あり）
Set-ExecutionPolicy RemoteSigned
Get-ExecutionPolicy

- pip install -r install.txt
- python main.py で実行

AttributeError: module 'serial' has no attribute 'Serial'
のエラーが出るので、
- pip uninstall serial
- pip install pyserial 
を実行する（もともとのserialライブラリが衝突している模様）
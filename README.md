ds18b20/
│
├── app.py                  # Flask本体
├── gps.py                  # GPS取得処理
├── temperature.py          # DS18B20水温取得
│
├── records/                # 計測CSV保存
│   ├── 20260801_212748.csv
│   └── ...
│
├── templates/
│   └── index.html          # Web画面
│
├── static/
│   │
│   ├── style.css           # Web画面デザイン
│   │
│   ├── script.js           # 地図・GPS表示・ボタン処理
│   │
│   ├── leaflet/            # Leaflet本体（現在配置済み）
│   │   ├── leaflet.css
│   │   ├── leaflet.js
│   │   └── images/
│   │       ├── marker-icon.png
│   │       ├── marker-icon-2x.png
│   │       └── marker-shadow.png
│   │
│   └── tiles/              # ★追加：オフライン地図
│       │
│       ├── 10/
│       │   └── {x}/
│       │       └── {y}.png
│       │
│       ├── 11/
│       │   └── {x}/
│       │       └── {y}.png
│       │
│       ├── 12/
│       │   └── {x}/
│       │       └── {y}.png
│       │
│       ├── 13/
│       │   └── {x}/
│       │       └── {y}.png
│       │
│       ├── 14/
│       │   └── {x}/
│       │       └── {y}.png
│       │
│       └── 15/
│           └── {x}/
│               └── {y}.png
│
├── env/                    # Python仮想環境
│
└── systemd設定（別場所）
    └── /etc/systemd/system/
        └── boat-monitor.service# -

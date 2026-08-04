# 水温計測システム（Raspberry Pi）

Raspberry Piを用いた水温・GPS計測システムです。
GPSによる位置情報取得、DS18B20による水温計測、Webブラウザからの計測操作・データ確認を行います。

## 概要

本システムでは以下の機能を実装しています。

* DS18B20による水温計測
* GPSによる位置情報取得
* GPS衛星数による測位状態確認
* 現在位置の地図表示
* 移動軌跡の表示
* 計測データのCSV保存
* Webブラウザからの計測開始・停止
* 保存したCSVデータのダウンロード
* Raspberry Pi起動時の自動起動対応

## システム構成

```
ds18b20/
│
├── app.py                  # Flaskメインプログラム
├── gps.py                  # GPSデータ取得処理
├── temperature.py          # DS18B20水温取得処理
├── requirements.txt        # Python依存ライブラリ
│
├── templates/
│   └── index.html          # Web画面
│
├── static/
│   ├── script.js           # Web画面制御・地図処理
│   ├── style.css           # Web画面デザイン
│   │
│   └── leaflet/            # Leaflet地図ライブラリ
│
├── records/                # 計測CSV保存先
│
└── env/                    # Python仮想環境
```

## 使用機器

* Raspberry Pi
* GPSモジュール（GT-502MGG-N）
* 水温センサ（DS18B20）
* Raspberry Pi Access Point環境
* Webブラウザ搭載端末（スマートフォン等）

## 動作環境

* Raspberry Pi OS
* Python 3.x
* Flask

## インストール

必要なライブラリをインストールします。

```bash
pip install -r requirements.txt
```

## 起動方法

### 手動起動

```bash
python app.py
```

起動後、ブラウザから以下へアクセスします。

```
http://raspberrypiのIPアドレス:5000
```

### 自動起動

systemdサービスとして登録することで、Raspberry Pi起動時に自動的に起動できます。

サービス：

```
boat-monitor.service
```

## CSVデータ

計測開始時に以下の形式でCSVファイルを作成します。

```
records/YYYYMMDD_HHMMSS.csv
```

保存データ：

| 項目          | 内容      |
| ----------- | ------- |
| time        | 計測時刻    |
| temperature | 水温      |
| latitude    | 緯度      |
| longitude   | 経度      |
| gps_fix     | GPS測位状態 |

## GPSについて

GPS測位には複数衛星からの信号が必要です。

表示内容：

* 捕捉衛星数
* 測位状態
* 緯度
* 経度

測位成功時には位置情報を記録します。

## 地図表示

Leafletを使用してGPS位置を表示します。

特徴：

* Raspberry Pi内にLeafletを保存
* ネットワーク接続なしでも動作可能
* オフライン地図タイル対応予定

## 注意事項

### 記録データ

`records/` 内のCSVファイルは実験データのため、Git管理対象外です。

### Python仮想環境

`env/` は環境依存ファイルのためGit管理対象外です。

## 今後の追加予定

* オフライン地図範囲拡張
* 現在位置と過去軌跡表示の切替UI
* 計測データ解析機能
* バッテリー駆動時間の最適化

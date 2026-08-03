import csv
import logging
import os
import threading
import time
import math
import json
import shutil
import subprocess
import uuid
import requests
from datetime import datetime

from flask import Flask, abort, jsonify, render_template, send_from_directory, request
from werkzeug.utils import secure_filename

from temperature import read_temperature
from gps import read_gps


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDS_DIR = os.path.join(BASE_DIR, "records")

CSV_HEADER = [
    "time",
    "temperature",
    "latitude",
    "longitude",
    "gps_fix"
]


os.makedirs(RECORDS_DIR, exist_ok=True)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger("water_temp_system")


app = Flask(__name__)


# -------------------------------
# グローバル状態(計測系)
# -------------------------------

lock = threading.Lock()


running = False

temperature = None

latitude = 0.0
longitude = 0.0
gps_fix = False
satellites = 0

gps_time = "--"

record_count = 0

filename = ""

message = "待機中"


csv_file = None
csv_writer = None



# -------------------------------
# 計測開始
# -------------------------------

def start_measurement():

    global running
    global filename
    global record_count
    global message
    global csv_file
    global csv_writer


    with lock:


        if running:
            return False, filename



        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )


        new_filename = timestamp + ".csv"


        filepath = os.path.join(
            RECORDS_DIR,
            new_filename
        )


        try:

            csv_file = open(
                filepath,
                "w",
                newline="",
                encoding="utf-8"
            )


            csv_writer = csv.writer(
                csv_file
            )


            csv_writer.writerow(
                CSV_HEADER
            )


            csv_file.flush()



        except OSError as exc:

            message = f"CSV作成エラー: {exc}"

            logger.error(message)

            return False, ""



        filename = new_filename

        record_count = 0

        running = True

        message = "計測中"


        logger.info(
            "計測開始: %s",
            filename
        )


        return True, filename




# -------------------------------
# 計測停止
# -------------------------------

def stop_measurement():

    global running
    global message
    global csv_file
    global csv_writer


    with lock:


        if not running:
            return False



        running = False

        message = "停止しました"



        if csv_file is not None:

            try:
                csv_file.close()

            except OSError as exc:

                logger.error(
                    "CSVクローズエラー: %s",
                    exc
                )

            finally:

                csv_file = None
                csv_writer = None



        logger.info(
            "計測終了: %s 件数=%d",
            filename,
            record_count
        )


        return True




# -------------------------------
# CSV保存
# -------------------------------

def write_record(
        temp_value,
        lat_value,
        lon_value,
        fix_value
):

    global record_count
    global message


    with lock:


        if not running:
            return


        if csv_writer is None:
            return



        # Raspberry Pi内部時計を使用
        now_str = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


        try:


            csv_writer.writerow(
                [
                    now_str,

                    temp_value
                    if temp_value is not None
                    else "",

                    lat_value,

                    lon_value,

                    fix_value
                ]
            )


            csv_file.flush()


            record_count += 1



        except OSError as exc:


            message = f"CSV書込エラー: {exc}"

            logger.error(message)




# -------------------------------
# GPSスレッド
# -------------------------------

def gps_worker():

    global latitude
    global longitude
    global gps_fix
    global gps_time
    global satellites


    while True:


        try:


            data = read_gps()


            with lock:


                latitude = data.get(
                    "latitude",
                    latitude
                )


                longitude = data.get(
                    "longitude",
                    longitude
                )


                gps_fix = data.get(
                    "gps_fix",
                    False
                )

                satellites = data.get(
                    "satellites",
                    0
                )

                gps_time = data.get(
                    "time",
                    gps_time
                )



        except Exception as exc:


            logger.error(
                "GPSスレッドエラー: %s",
                exc
            )


            with lock:

                gps_fix = False


# -------------------------------
# 計測スレッド
# -------------------------------

def measurement_worker():

    global temperature
    global message

    while True:

        start = time.time()

        try:

            # 常時水温取得
            temp_value = read_temperature()


            with lock:

                temperature = temp_value


                lat_value = latitude

                lon_value = longitude

                fix_value = gps_fix



            # 計測中のみCSV保存
            if running:

                write_record(
                    temp_value,
                    lat_value,
                    lon_value,
                    fix_value
                )


        except Exception as exc:


            logger.error(
                "計測スレッドエラー: %s",
                exc
            )


            with lock:

                message = f"計測エラー: {exc}"



        elapsed = time.time() - start


        time.sleep(
            max(0, 1 - elapsed)
        )



# =========================================================
# オフライン地図(名前付き・リージョン管理)
# =========================================================

MAPS_ROOT = os.path.join(BASE_DIR, "static", "maps", "regions")
os.makedirs(MAPS_ROOT, exist_ok=True)

META_PATH = os.path.join(BASE_DIR, "static", "maps", "meta.json")

TILE_SERVER_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
TILE_REQUEST_HEADERS = {"User-Agent": "negi-boat-offline-map/1.0 (research use)"}

MIN_DOWNLOAD_ZOOM = 13
MAX_DOWNLOAD_ZOOM = 18

MAX_TOTAL_BYTES = 5 * 1024 * 1024 * 1024  # 5GB上限

maps_lock = threading.Lock()

download_state = {
    "running": False,
    "region_id": None,
    "name": "",
    "total": 0,
    "done": 0,
    "skipped": 0,
    "failed": 0,
    "message": "待機中",
    "cancel_requested": False,
}


def load_meta():
    if not os.path.isfile(META_PATH):
        return {}
    try:
        with open(META_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_meta(meta):
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def get_dir_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for name in filenames:
            fp = os.path.join(dirpath, name)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def get_total_maps_size():
    if not os.path.isdir(MAPS_ROOT):
        return 0
    return get_dir_size(MAPS_ROOT)


def is_wired_connection():
    # eth0, end0 などの有線LANポートでリンクアップ(ケーブル接続)しているか直接確認
    for iface in ["eth0", "end0", "eth1"]:
        carrier_path = f"/sys/class/net/{iface}/carrier"
        if os.path.exists(carrier_path):
            try:
                with open(carrier_path, "r") as f:
                    if f.read().strip() == "1":
                        return True
            except Exception:
                pass
    return False

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x = int((lon_deg + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def build_tile_list(south, west, north, east, min_zoom, max_zoom):
    tasks = []
    for z in range(min_zoom, max_zoom + 1):
        x_min, y_max = deg2num(south, west, z)
        x_max, y_min = deg2num(north, east, z)
        for x in range(min(x_min, x_max), max(x_min, x_max) + 1):
            for y in range(min(y_min, y_max), max(y_min, y_max) + 1):
                tasks.append((z, x, y))
    return tasks


@app.route("/tiles/<int:z>/<int:x>/<int:y>.png")
def serve_tile(z, x, y):

    meta = load_meta()

    for region_id, info in meta.items():

        if info.get("status") != "completed":
            continue

        tile_path = os.path.join(
            MAPS_ROOT, region_id, str(z), str(x), f"{y}.png"
        )

        if os.path.isfile(tile_path):
            return send_from_directory(
                os.path.join(MAPS_ROOT, region_id, str(z), str(x)),
                f"{y}.png"
            )

    abort(404)


def download_tiles_worker(region_id, name, tasks, bbox):

    global download_state

    region_dir = os.path.join(MAPS_ROOT, region_id)
    os.makedirs(region_dir, exist_ok=True)

    with maps_lock:
        download_state.update({
            "running": True,
            "region_id": region_id,
            "name": name,
            "total": len(tasks),
            "done": 0,
            "skipped": 0,
            "failed": 0,
            "message": "ダウンロード中",
            "cancel_requested": False,
        })

    meta = load_meta()
    meta[region_id] = {
        "name": name,
        "status": "downloading",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "bbox": bbox,
        "tile_count": 0,
        "size_bytes": 0,
    }
    save_meta(meta)

    cancelled = False

    for z, x, y in tasks:

        with maps_lock:
            if download_state["cancel_requested"]:
                cancelled = True

        if cancelled:
            break

        if get_total_maps_size() > MAX_TOTAL_BYTES:
            with maps_lock:
                download_state["message"] = "容量上限に達したため中断しました"
            break

        tile_dir = os.path.join(region_dir, str(z), str(x))
        tile_path = os.path.join(tile_dir, f"{y}.png")

        try:
            url = TILE_SERVER_URL.format(z=z, x=x, y=y)
            response = requests.get(url, headers=TILE_REQUEST_HEADERS, timeout=10)
            if response.status_code == 200:
                os.makedirs(tile_dir, exist_ok=True)
                with open(tile_path, "wb") as f:
                    f.write(response.content)
            else:
                with maps_lock:
                    download_state["failed"] += 1
        except requests.RequestException as exc:
            logger.error("タイル取得エラー: %s", exc)
            with maps_lock:
                download_state["failed"] += 1

        with maps_lock:
            download_state["done"] += 1

        time.sleep(0.2)

    if cancelled:
        shutil.rmtree(region_dir, ignore_errors=True)
        meta = load_meta()
        meta.pop(region_id, None)
        save_meta(meta)

        with maps_lock:
            download_state["running"] = False
            download_state["message"] = "キャンセルしました"

        logger.info("地図ダウンロードをキャンセル: %s", name)
        return

    size_bytes = get_dir_size(region_dir)
    meta = load_meta()
    meta[region_id]["status"] = "completed"
    meta[region_id]["size_bytes"] = size_bytes
    meta[region_id]["tile_count"] = download_state["done"] - download_state["failed"]
    save_meta(meta)

    with maps_lock:
        download_state["running"] = False
        download_state["message"] = "完了"


@app.route("/maps/download", methods=["POST"])
def maps_download():

    if not is_wired_connection():
        return jsonify({
            "success": False,
            "message": "有線LAN接続時のみ地図を保存できます"
        })

    with maps_lock:
        if download_state["running"]:
            return jsonify({"success": False, "message": "既にダウンロード中です"})

    data = request.get_json()

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "message": "地図名を入力してください"})

    if get_total_maps_size() > MAX_TOTAL_BYTES:
        return jsonify({
            "success": False,
            "message": "容量上限に達しています。不要な地図を削除してください"
        })

    south, west = data["south"], data["west"]
    north, east = data["north"], data["east"]

    tasks = build_tile_list(south, west, north, east, MIN_DOWNLOAD_ZOOM, MAX_DOWNLOAD_ZOOM)

    region_id = uuid.uuid4().hex[:12]

    threading.Thread(
        target=download_tiles_worker,
        args=(region_id, name, tasks, {"south": south, "west": west, "north": north, "east": east}),
        daemon=True
    ).start()

    return jsonify({"success": True, "total": len(tasks), "region_id": region_id})


@app.route("/maps/download/status")
def maps_download_status():
    with maps_lock:
        return jsonify(dict(download_state))


@app.route("/maps/download/cancel", methods=["POST"])
def maps_download_cancel():
    with maps_lock:
        if not download_state["running"]:
            return jsonify({"success": False, "message": "ダウンロード中ではありません"})
        download_state["cancel_requested"] = True
    return jsonify({"success": True})


@app.route("/maps/regions")
def maps_regions():

    meta = load_meta()

    regions = []
    for region_id, info in meta.items():
        regions.append({
            "id": region_id,
            "name": info.get("name", ""),
            "status": info.get("status", ""),
            "size_bytes": info.get("size_bytes", 0),
            "tile_count": info.get("tile_count", 0),
            "created_at": info.get("created_at", ""),
        })

    total_bytes = get_total_maps_size()

    return jsonify({
        "regions": regions,
        "total_bytes": total_bytes,
        "limit_bytes": MAX_TOTAL_BYTES,
    })


@app.route("/maps/regions/<region_id>", methods=["DELETE"])
def maps_region_delete(region_id):

    region_dir = os.path.join(MAPS_ROOT, region_id)

    if os.path.isdir(region_dir):
        shutil.rmtree(region_dir, ignore_errors=True)

    meta = load_meta()
    meta.pop(region_id, None)
    save_meta(meta)

    return jsonify({"success": True})



# -------------------------------
# Flask(計測系ルート)
# -------------------------------

@app.route("/")
def index():

    return render_template(
        "index.html"
    )



@app.route("/status")
def status():

    with lock:

        return jsonify(
            {
                "running": running,

                "temperature": temperature,

                "latitude": latitude,

                "longitude": longitude,

                "gps_fix": gps_fix,

                "records": record_count,

                "filename": filename,

                "message": message,

                "satellites": satellites,

                "current_time":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
            }
        )




@app.route("/start", methods=["POST"])
def start():

    success, fname = start_measurement()

    return jsonify(
        {
            "success": success,
            "filename": fname
        }
    )




@app.route("/stop", methods=["POST"])
def stop():

    success = stop_measurement()

    return jsonify(
        {
            "success": success
        }
    )




@app.route("/files")
def files():

    csv_files = [

        f for f in os.listdir(RECORDS_DIR)

        if f.lower().endswith(".csv")

    ]


    csv_files.sort(
        reverse=True
    )


    return jsonify(
        {
            "files": csv_files
        }
    )


# -------------------------------
# 現在位置取得
# -------------------------------

@app.route("/gps_current")
def gps_current():

    with lock:

        return jsonify(
            {
                "latitude": latitude,
                "longitude": longitude,
                "gps_fix": gps_fix
            }
        )



# -------------------------------
# CSV軌跡取得
# -------------------------------

@app.route("/track/<path:requested_filename>")
def track(requested_filename):

    safe_name = secure_filename(
        requested_filename
    )


    filepath = os.path.join(
        RECORDS_DIR,
        safe_name
    )


    if (
        not safe_name.lower().endswith(".csv")
        or not os.path.isfile(filepath)
    ):
        abort(404)



    points = []


    try:

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as f:


            reader = csv.DictReader(f)


            for row in reader:


                try:

                    lat = float(
                        row["latitude"]
                    )

                    lon = float(
                        row["longitude"]
                    )


                    # GPS Fixなしは除外
                    if (
                        lat == 0.0
                        or lon == 0.0
                    ):
                        continue


                    points.append(
                        [
                            lat,
                            lon
                        ]
                    )


                except (
                    ValueError,
                    KeyError
                ):
                    continue



    except OSError as exc:

        logger.error(
            "軌跡読み込みエラー: %s",
            exc
        )

        abort(500)



    return jsonify(
        {
            "points": points
        }
    )

@app.route("/download/<path:requested_filename>")
def download(requested_filename):

    safe_name = secure_filename(
        requested_filename
    )


    filepath = os.path.join(
        RECORDS_DIR,
        safe_name
    )


    if (
        not safe_name.lower().endswith(".csv")
        or not os.path.isfile(filepath)
    ):

        abort(404)



    return send_from_directory(
        RECORDS_DIR,
        safe_name,
        as_attachment=True
    )


@app.route("/network/status")
def network_status():
    return jsonify({"wired": is_wired_connection()})

# -------------------------------
# 起動
# -------------------------------

if __name__ == "__main__":


    threading.Thread(
        target=gps_worker,
        daemon=True
    ).start()



    threading.Thread(
        target=measurement_worker,
        daemon=True
    ).start()



    logger.info(
        "バックグラウンドスレッドを開始しました"
    )


    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

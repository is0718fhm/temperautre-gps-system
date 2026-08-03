import logging
import time
import subprocess
from datetime import datetime, timedelta

import serial
import pynmea2

logger = logging.getLogger("water_temp_system.gps")


# -------------------------------
# GPSシリアル初期化
# -------------------------------
try:
    ser = serial.Serial(
        "/dev/serial0",
        baudrate=9600,
        timeout=0.2
    )

except (serial.SerialException, OSError) as exc:
    logger.error("GPSシリアルポートを開けません: %s", exc)
    ser = None


# -------------------------------
# 状態保持
# -------------------------------
last_data = {
    "latitude": 0.0,
    "longitude": 0.0,
    "time": "--",
    "gps_fix": False,
    "satellites": 0,
}

# Raspberry Pi時計補正済みフラグ
time_synced = False



# -------------------------------
# Raspberry Pi時計補正
# -------------------------------
def set_system_time(jst_time):
    """
    GPS時刻でRaspberry Pi内部時計を補正
    """

    try:
        subprocess.run(
            [
                "sudo",
                "date",
                "-s",
                jst_time
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        logger.info(
            "Raspberry Pi時計補正成功: %s",
            jst_time
        )

        return True


    except subprocess.CalledProcessError as exc:

        logger.error(
            "Raspberry Pi時計補正失敗: %s",
            exc
        )

        return False



# -------------------------------
# GPS取得
# -------------------------------
def read_gps():

    global last_data
    global time_synced

    # 一旦Fixなし
    last_data["gps_fix"] = False

    if ser is None:
        return last_data

    start = time.time()

    while time.time() - start < 1.0:

        try:

            line = ser.readline().decode(
                "ascii",
                errors="ignore"
            )

        except (serial.SerialException, OSError) as exc:

            logger.error(
                "GPSシリアルエラー: %s",
                exc
            )

            break

        # -------------------------------
        # GGA（衛星数取得）
        # -------------------------------
        if line.startswith("$GNGGA") or line.startswith("$GPGGA"):

            try:

                msg = pynmea2.parse(line)

                last_data["satellites"] = int(
                    msg.num_sats or 0
                )

            except (
                pynmea2.ParseError,
                TypeError,
                ValueError
            ):
                pass

        # -------------------------------
        # RMC（位置・時刻取得）
        # -------------------------------
        if line.startswith("$GNRMC") or line.startswith("$GPRMC"):

            try:

                msg = pynmea2.parse(line)

                # A = Fix成功
                if msg.status == "A":

                    # UTC → JST
                    utc = datetime.combine(
                        msg.datestamp,
                        msg.timestamp
                    )

                    jst = utc + timedelta(hours=9)

                    jst_string = jst.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    # 初回Fix時のみ時計補正
                    if not time_synced:

                        if set_system_time(jst_string):
                            time_synced = True

                    last_data = {

                        "latitude":
                            msg.latitude,

                        "longitude":
                            msg.longitude,

                        "time":
                            jst_string,

                        "gps_fix":
                            True,

                        "satellites":
                            last_data["satellites"],
                    }

                    break

            except (
                pynmea2.ParseError,
                TypeError,
                ValueError
            ):
                pass

    return last_data

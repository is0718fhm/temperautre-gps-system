from w1thermsensor import W1ThermSensor, NoSensorFoundError, SensorNotReadyError

# センサーは起動時に一度だけ初期化を試みる（元のプロトタイプと同じ方式）
try:
    sensor = W1ThermSensor()
except NoSensorFoundError:
    sensor = None


def read_temperature():
    """水温(℃)を取得する。センサー未接続・読み取り失敗時は None を返す。"""
    global sensor

    if sensor is None:
        try:
            sensor = W1ThermSensor()
        except NoSensorFoundError:
            return None

    try:
        return round(sensor.get_temperature(), 2)
    except (NoSensorFoundError, SensorNotReadyError):
        return None

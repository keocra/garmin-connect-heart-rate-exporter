import json
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime
from glob import glob


HEART_RATE_FOLDER = "./2016-07-17_garmin_connect_export/"
HEART_RATE_FILE_PATTERN = "*.json"


def plot_heart_rates(heart_rates):
    keys = []
    values = []
    for heart_rate in heart_rates:
        keys.append(datetime.fromtimestamp(float(heart_rate["timestampMs"]) / 1000).strftime("%Y-%m-%dT%H:%M:%S"))
        values.append(heart_rate["heart_rate"])

    index = np.arange(len(keys))
    plt.plot(index, values)

    title = "heart_rate bpm curve"

    plt.xlabel("timestamp seconds")
    plt.ylabel("heart_rate bpm")
    plt.title(title)
    plt.gcf().canvas.set_window_title(title)

    plt.xticks(np.arange(0, len(keys), len(keys) / len(keys[0::800]) + 2), keys[0::800])

    plt.show()


def join_dicts(d1, d2):
    tmp = d1.copy()
    tmp.update(d2)
    return tmp


def plot_average_per_day_heart_rate(heart_rates):
    per_day_heart_rate = {}
    for heart_rate in heart_rates:
        if heart_rate["heart_rate"]:
            day = datetime.fromtimestamp(float(heart_rate["timestampMs"]) / 1000).strftime("%Y-%m-%d")

            if day not in per_day_heart_rate:
                per_day_heart_rate[day] = {"sum_bpm": 0, "day": day, "count": 0}

            per_day_heart_rate[day]["sum_bpm"] += heart_rate["heart_rate"]
            per_day_heart_rate[day]["count"] += 1

    per_day_heart_rate = sorted(per_day_heart_rate.values(), key=lambda x: x["day"])
    per_day_heart_rate = map(lambda x: join_dicts({"average_bpm": x["sum_bpm"] / x["count"]}, x), per_day_heart_rate)

    values = []
    keys = []
    for heart_rate in per_day_heart_rate:
        values.append(heart_rate["average_bpm"])
        keys.append(heart_rate["day"])

    index = np.arange(len(keys))
    plt.plot(index, values)

    title = "average heart_rate bpm curve"

    plt.xlabel("timestamp seconds")
    plt.ylabel("heart_rate bpm")
    plt.title(title)
    plt.gcf().canvas.set_window_title(title)

    plt.xticks(np.arange(0, len(keys), len(keys) / len(keys[0::10]) + 2), keys[0::10])

    plt.show()


def main():
    heart_rate_files = glob(HEART_RATE_FOLDER + HEART_RATE_FILE_PATTERN)

    heart_rates = []
    for heart_rate_file in heart_rate_files:
        with open(heart_rate_file) as fh:
            heart_rate_data = json.load(fh)

        for heart_rate in heart_rate_data["heartRateValues"]:
            heart_rates.append({
                "timestampMs": heart_rate[0],
                "heart_rate": heart_rate[1]
            })

    # make sure the heart rates are sorted
    heart_rates = sorted(heart_rates, key=lambda x: x["timestampMs"])

    for heart_rate in heart_rates:
        print datetime.fromtimestamp(float(heart_rate["timestampMs"]) // 1000).strftime("%Y-%m-%d %H:%M:%S"), "heart_rate:", heart_rate["heart_rate"]

    plot_heart_rates(heart_rates)
    plot_average_per_day_heart_rate(heart_rates)


if __name__ == "__main__":
    main()

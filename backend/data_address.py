import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config


class DataProcessor:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        # 系统支持的指标维度
        self.metrics = ["temperature", "humidity", "pressure"]

    def predict_series(self, df, column, points=5):
        """
        对单个时间序列做线性回归拟合与简单预测
        """
        if column not in df.columns:
            return [], []

        y = df[column].values
        if len(y) < 2:
            return [], []

        X = np.arange(len(y)).reshape(-1, 1)

        model = LinearRegression()
        model.fit(X, y)

        fitted = model.predict(X).tolist()
        future_X = np.arange(len(y), len(y) + points).reshape(-1, 1)
        future = model.predict(future_X).tolist()

        return fitted, future

    def process(self):
        # ----------------------------------------------------
        # CSV 文件检查
        # ----------------------------------------------------
        if not os.path.exists(self.csv_path):
            return {"error": "Wait for data... CSV file not found."}

        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            return {"error": f"Read CSV failed: {str(e)}"}

        if df.empty or len(df) < 2:
            return {"error": "Need more data points for analysis."}

        # ----------------------------------------------------
        # 判断实际存在的指标（兼容未订阅情况）
        # ----------------------------------------------------
        available_metrics = [m for m in self.metrics if m in df.columns]
        if not available_metrics:
            return {"error": "No valid sensor data found."}

        # 转换为数值类型
        for m in available_metrics:
            df[m] = pd.to_numeric(df[m], errors="coerce")

        df = df.dropna(subset=available_metrics)

        if df.empty:
            return {"error": "All sensor data is invalid after cleaning."}

        # ----------------------------------------------------
        # 基础统计
        # ----------------------------------------------------
        stats = {}
        for m in available_metrics:
            stats[m] = {
                "max": float(df[m].max()),
                "min": float(df[m].min()),
                "avg": float(df[m].mean().round(2))
            }

        stats["current_count"] = len(df)

        # ----------------------------------------------------
        # 趋势分析（最近 30 个点，滑动平均）
        # ----------------------------------------------------
        plot_df = df.tail(30).copy()

        for m in available_metrics:
            plot_df[f"{m}_smooth"] = plot_df[m].rolling(
                window=5, min_periods=1
            ).mean()

        # ----------------------------------------------------
        # 简单预测（线性回归）
        # ----------------------------------------------------
        analysis_result = {}

        for m in available_metrics:
            fitted, predicted = self.predict_series(plot_df, m)
            analysis_result[m] = {
                "raw": plot_df[m].tolist(),
                "smooth": plot_df[f"{m}_smooth"].tolist(),
                "fitted": fitted,
                "predict": predicted
            }

        # ----------------------------------------------------
        # 相关性分析（至少两个维度才有意义）
        # ----------------------------------------------------
        correlation = {}
        if len(available_metrics) >= 2:
            correlation = (
                df[available_metrics]
                .corr()
                .round(2)
                .to_dict()
            )

        # ----------------------------------------------------
        # 时间格式处理
        # ----------------------------------------------------
        if "timestamp" in plot_df.columns:
            plot_df["timestamp"] = pd.to_datetime(
                plot_df["timestamp"],
                errors="coerce"
            )

            # 转成更短、更适合图表的格式
            plot_df["timestamp_fmt"] = plot_df["timestamp"].dt.strftime(
                "%m-%d %H:%M")
        else:
            plot_df["timestamp_fmt"] = list(range(len(plot_df)))

        # ----------------------------------------------------
        # 返回统一结构，直接给前端
        # ----------------------------------------------------
        return {
            "stats": stats,
            "data": analysis_result,
            "labels": plot_df["timestamp_fmt"].tolist(),
            "correlation": correlation,
            "available_metrics": available_metrics
        }


app = Flask(__name__)
# 配置CORS以允许跨域请求
CORS(app, resources={r"/*": {"origins": "*",
     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, "sensor_data.csv")

processor = DataProcessor(CSV_PATH)


@app.route("/api/analyze", methods=["GET"])
def analyze_data():
    try:
        result = processor.process()
        return jsonify(result)
    except Exception as e:
        print(f"分析服务错误: {str(e)}")
        return jsonify({"error": f"分析服务错误: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host=Config.ANALYSIS_SERVICE_HOST,
            port=Config.ANALYSIS_SERVICE_PORT, debug=True, threaded=True)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪器设备管理系统后端服务
支持从Excel导入设备总览表
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time
import urllib.parse

# 数据存储路径
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
LOGS_DIR = BASE_DIR / "logs"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# 数据文件路径
INSTRUMENTS_FILE = DATA_DIR / "instruments.json"
RECORDS_FILE = DATA_DIR / "records.json"
HISTORY_FILE = DATA_DIR / "history.json"

# 从Excel导入的仪器数据（测试间仪器设备总览表_202502.xlsx）
INSTRUMENTS_FROM_EXCEL = [
    {
        "id": 1,
        "name": "示波器",
        "model": "EXR208A",
        "brand": "KEYSIGHT",
        "params": "2GHz，8通道",
        "quantity": 2,
        "available": 2,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 2,
        "name": "示波器",
        "model": "DSOX4154A",
        "brand": "KEYSIGHT",
        "params": "1.5GHz，4通道",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 3,
        "name": "示波器",
        "model": "UXR0104B",
        "brand": "KEYSIGHT",
        "params": "10GHz4通道3.5mm输入",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 4,
        "name": "示波器",
        "model": "SDS3104X HD",
        "brand": "SIGLENT",
        "params": "1GHz，4通道",
        "quantity": 2,
        "available": 2,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 5,
        "name": "波形发生器",
        "model": "33622A",
        "brand": "KEYSIGHT",
        "params": "120 MHz，2 通道",
        "quantity": 3,
        "available": 3,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 6,
        "name": "电子负载",
        "model": "EL34243A",
        "brand": "KEYSIGHT",
        "params": "150V/60A/300W",
        "quantity": 2,
        "available": 2,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 7,
        "name": "电子负载",
        "model": "IT8512C+",
        "brand": "IT8512C+",
        "params": "120V/60A/300W",
        "quantity": 2,
        "available": 2,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 8,
        "name": "电子负载",
        "model": "63600-5",
        "brand": "CHROMA",
        "params": "5个模组，每个模组最高400W/600V/80A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 9,
        "name": "超低压直流电子负载",
        "model": "63202A-20-2000",
        "brand": "CHROMA",
        "params": "2kW/0.25V2000A/20V",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 10,
        "name": "功率分析仪",
        "model": "PA2201A",
        "brand": "KEYSIGHT",
        "params": "2通道/单相交流",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 11,
        "name": "交流电源",
        "model": "6811C",
        "brand": "KEYSIGHT",
        "params": "375 VA/300 V/3.25 A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 12,
        "name": "频谱分析仪",
        "model": "MS2850A",
        "brand": "ANRISTU",
        "params": "最大分析带宽：1 GHz",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 13,
        "name": "台式万用表",
        "model": "34465A",
        "brand": "KEYSIGHT",
        "params": "六位半",
        "quantity": 6,
        "available": 6,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 14,
        "name": "台式万用表",
        "model": "3458A",
        "brand": "KEYSIGHT",
        "params": "八位半",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 15,
        "name": "直流电源",
        "model": "E36313A",
        "brand": "KEYSIGHT",
        "params": "160W三路输出/6V，10A 和 2X 25V，2A",
        "quantity": 6,
        "available": 6,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 16,
        "name": "直流电源",
        "model": "N5772A",
        "brand": "KEYSIGHT",
        "params": "600V，2.6A，1560W",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 17,
        "name": "直流电源",
        "model": "E36155A",
        "brand": "KEYSIGHT",
        "params": "60 V，40 A，800 W",
        "quantity": 3,
        "available": 3,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 18,
        "name": "直流电源",
        "model": "N8957A",
        "brand": "KEYSIGHT",
        "params": "1500 V，30 A，15000 W，400 VAC",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 19,
        "name": "直流电源分析仪",
        "model": "N6705C",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 20,
        "name": "源表",
        "model": "B2902B",
        "brand": "KEYSIGHT",
        "params": "2 通道，100 fA 分辨率，210 V，3 A 直流/10.5 A 脉冲",
        "quantity": 2,
        "available": 2,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 21,
        "name": "信号源",
        "model": "SDG2042X",
        "brand": "SIGLENT",
        "params": "最大输出频率40 MHz，1.2 GSa/s采样率",
        "quantity": 2,
        "available": 2,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 22,
        "name": "交流电源",
        "model": "6811C",
        "brand": "KEYSIGHT",
        "params": "375 VA，300 V，3.25 A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 23,
        "name": "温箱",
        "model": "STH-120",
        "brand": "ESPEC",
        "params": "+20～+200℃",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 24,
        "name": "电源",
        "model": "DH1766-3",
        "brand": "DH大华",
        "params": "200W~360W",
        "quantity": 4,
        "available": 4,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 25,
        "name": "热像仪",
        "model": "U5855A",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 26,
        "name": "矢量网络分析仪",
        "model": "N7550A",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 27,
        "name": "绝缘测试仪",
        "model": "GPT-9803",
        "brand": "GWINSTEK",
        "params": "N/A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 28,
        "name": "频率计",
        "model": "53230A",
        "brand": "KEYSIGHT",
        "params": "350 MHz 12 位/秒，20 ps",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 29,
        "name": "环路分析仪",
        "model": "Bode100",
        "brand": "Bode100",
        "params": "1 Hz到50 MHz",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 30,
        "name": "脉冲函数任意噪声发生器",
        "model": "81160A",
        "brand": "KEYSIGHT",
        "params": "脉冲频率高达 120 MHz 和正弦频率高达 240 MHz",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    {
        "id": 31,
        "name": "LCR表",
        "model": "TH2840B",
        "brand": "Tonghui",
        "params": "N/A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
    },
    # ========== Sheet2 探头/配件 ==========
    {
        "id": 101,
        "name": "电流探头",
        "model": "N7020A",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 2,
        "available": 2,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 102,
        "name": "电流探头",
        "model": "N7026A",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 4,
        "available": 4,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 103,
        "name": "电流探头",
        "model": "1134B",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 2,
        "available": 2,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 104,
        "name": "电流探头",
        "model": "N2783B",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 105,
        "name": "电流探头供电单元",
        "model": "N2779A",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 106,
        "name": "差分探头",
        "model": "DP0001A",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 2,
        "available": 2,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 107,
        "name": "光隔离探头",
        "model": "MOI1000P",
        "brand": "Micsig",
        "params": "N/A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 108,
        "name": "探头前端",
        "model": "E2669B",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 109,
        "name": "探头前端",
        "model": "E2675B",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 110,
        "name": "无源探头",
        "model": "10076C",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 6,
        "available": 6,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 111,
        "name": "无源探头",
        "model": "N2870A",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 1,
        "available": 1,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 112,
        "name": "有源探头",
        "model": "MX0020A",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 2,
        "available": 2,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
    {
        "id": 113,
        "name": "微型探头套件",
        "model": "MX0100A",
        "brand": "KEYSIGHT",
        "params": "N/A",
        "quantity": 5,
        "available": 5,
        "status": "available",
        "currentUsers": [],
        "location": "测试间",
        "category": "探头",
    },
]


def load_data():
    """加载数据"""
    instruments = []
    records = []
    history = []

    if INSTRUMENTS_FILE.exists():
        with open(INSTRUMENTS_FILE, "r", encoding="utf-8") as f:
            instruments = json.load(f)
    elif INSTRUMENTS_FROM_EXCEL:
        instruments = INSTRUMENTS_FROM_EXCEL.copy()
        save_instruments(instruments)
    else:
        # 默认示例数据
        instruments = get_default_instruments()
        save_instruments(instruments)

    if RECORDS_FILE.exists():
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)

    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    return instruments, records, history


def get_default_instruments():
    """获取默认仪器数据 - 等待从Excel导入"""
    return [
        {
            "id": 1,
            "name": "信号发生器",
            "model": "DSG830",
            "quantity": 2,
            "available": 2,
            "status": "available",
            "currentUsers": [],
            "location": "测试间A",
        },
        {
            "id": 2,
            "name": "电子负载",
            "model": "IT8512B",
            "quantity": 3,
            "available": 3,
            "status": "available",
            "currentUsers": [],
            "location": "测试间A",
        },
        {
            "id": 3,
            "name": "示波器",
            "model": "MSO5104",
            "quantity": 2,
            "available": 2,
            "status": "available",
            "currentUsers": [],
            "location": "测试间A",
        },
        {
            "id": 4,
            "name": "万用表",
            "model": "34461A",
            "quantity": 5,
            "available": 5,
            "status": "available",
            "currentUsers": [],
            "location": "测试间A",
        },
        {
            "id": 5,
            "name": "直流电源",
            "model": "DP832",
            "quantity": 4,
            "available": 4,
            "status": "available",
            "currentUsers": [],
            "location": "测试间A",
        },
        {
            "id": 6,
            "name": "频谱分析仪",
            "model": "RSA3030E",
            "quantity": 1,
            "available": 1,
            "status": "available",
            "currentUsers": [],
            "location": "测试间B",
        },
        {
            "id": 7,
            "name": "网络分析仪",
            "model": "E5061B",
            "quantity": 1,
            "available": 1,
            "status": "available",
            "currentUsers": [],
            "location": "测试间B",
        },
        {
            "id": 8,
            "name": "LCR测试仪",
            "model": "E4980A",
            "quantity": 1,
            "available": 1,
            "status": "available",
            "currentUsers": [],
            "location": "测试间B",
        },
    ]


def save_instruments(instruments):
    """保存仪器数据"""
    with open(INSTRUMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(instruments, f, ensure_ascii=False, indent=2)


def save_records(records):
    """保存记录数据"""
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def save_history(history):
    """保存历史记录"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def backup_data():
    """备份数据"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_subdir = BACKUP_DIR / f"backup_{timestamp}"
    backup_subdir.mkdir(exist_ok=True)

    # 复制所有数据文件
    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as src:
            content = src.read()
        with open(backup_subdir / file.name, "w", encoding="utf-8") as dst:
            dst.write(content)

    # 记录备份日志
    log_file = LOGS_DIR / "backup.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 数据已备份到: {backup_subdir}\n"
        )

    print(f"✅ 数据已备份到: {backup_subdir}")
    return str(backup_subdir)


def check_and_update_status():
    """检查并更新仪器状态"""
    instruments, records, history = load_data()
    now = datetime.now()
    updated = False

    for record in records:
        try:
            end_time_str = (
                record["endTime"].replace("Z", "+00:00").replace("+00:00", "")
            )
            end_time = datetime.fromisoformat(end_time_str)
            if end_time <= now:
                # 释放仪器
                for inst_id in record["instrumentIds"]:
                    inst = next((i for i in instruments if i["id"] == inst_id), None)
                    if inst:
                        # 从当前用户列表中移除
                        if record["userName"] in inst.get("currentUsers", []):
                            inst["currentUsers"] = [
                                u
                                for u in inst["currentUsers"]
                                if u != record["userName"]
                            ]
                            inst["available"] = inst.get("available", 0) + 1
                            if inst["available"] >= inst["quantity"]:
                                inst["status"] = "available"
                            updated = True
        except:
            pass

    if updated:
        save_instruments(instruments)
        print(f"✅ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已自动释放到期仪器")


class APIHandler(SimpleHTTPRequestHandler):
    """HTTP请求处理器 - 支持API和静态文件"""

    def __init__(self, *args, **kwargs):
        # 设置静态文件目录
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """处理GET请求"""
        # API路由
        if self.path.startswith("/api/"):
            if self.path == "/api/instruments":
                self.send_json_response(self.get_instruments())
            elif self.path == "/api/records":
                self.send_json_response(self.get_records())
            elif self.path == "/api/history":
                self.send_json_response(self.get_history())
            elif self.path == "/api/stats":
                self.send_json_response(self.get_stats())
            else:
                self.send_error(404)
        else:
            # 静态文件服务
            super().do_GET()

    def do_POST(self):
        """处理POST请求"""
        if self.path == "/api/register":
            self.handle_register()
        elif self.path == "/api/release":
            self.handle_release()
        else:
            self.send_error(404)

    def send_json_response(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def get_instruments(self):
        """获取仪器列表"""
        instruments, _, _ = load_data()
        return {"success": True, "data": instruments}

    def get_records(self):
        """获取当前记录"""
        _, records, _ = load_data()
        from datetime import timezone

        now = datetime.now(timezone.utc)
        active_records = []
        for r in records:
            try:
                end_time_str = r["endTime"]
                # 检查是否带有时区信息
                if "+" in end_time_str or "Z" in end_time_str:
                    # 带时区的时间
                    end_time_str = end_time_str.replace("Z", "+00:00")
                    end_time = datetime.fromisoformat(end_time_str)
                else:
                    # 无时区的时间（旧数据，假设为本地时间UTC+8）
                    end_time = datetime.fromisoformat(end_time_str)
                    # 转换为UTC（减去8小时）
                    end_time = end_time.replace(tzinfo=timezone.utc) - timedelta(hours=8)

                if end_time > now:
                    active_records.append(r)
            except Exception as e:
                print(f"解析时间出错: {e}, endTime: {r.get('endTime')}")
                pass
        return {"success": True, "data": active_records}

    def get_history(self):
        """获取历史记录"""
        _, _, history = load_data()
        return {"success": True, "data": history[-100:]}  # 返回最近100条

    def get_stats(self):
        """获取统计信息"""
        instruments, _, _ = load_data()
        total = sum(i["quantity"] for i in instruments)
        available = sum(i.get("available", 0) for i in instruments)
        in_use = total - available

        return {
            "success": True,
            "data": {"total": total, "available": available, "inUse": in_use},
        }

    def handle_register(self):
        """处理登记请求"""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode("utf-8"))

            # 验证必填字段
            required = [
                "userName",
                "userDept",
                "userContact",
                "instrumentIds",
                "startTime",
                "endTime",
                "purpose",
            ]
            for field in required:
                if field not in data or not data[field]:
                    self.send_json_response(
                        {"success": False, "error": f"缺少必填字段: {field}"}
                    )
                    return

            instruments, records, history = load_data()

            # 获取数量信息（兼容旧版本）
            quantities = data.get("instrumentQuantities", {})
            if not quantities:
                # 如果没有提供数量，默认每台仪器使用1台
                quantities = {str(inst_id): 1 for inst_id in data["instrumentIds"]}

            # 检查仪器是否可用且数量足够
            for inst_id in data["instrumentIds"]:
                inst = next((i for i in instruments if i["id"] == inst_id), None)
                if not inst:
                    self.send_json_response(
                        {"success": False, "error": f"仪器不存在: ID {inst_id}"}
                    )
                    return

                requested_qty = quantities.get(str(inst_id), 1)
                available_qty = inst.get("available", inst.get("quantity", 0))

                if available_qty < requested_qty:
                    self.send_json_response(
                        {
                            "success": False,
                            "error": f"仪器 {inst['name']} ({inst['model']}) 可用数量不足，仅剩 {available_qty} 台，请求 {requested_qty} 台",
                        }
                    )
                    return

            # 创建记录
            record = {
                "id": int(datetime.now(timezone.utc).timestamp() * 1000),
                "registerTime": datetime.now(timezone.utc).isoformat(),
                "userName": data["userName"],
                "userDept": data["userDept"],
                "userContact": data["userContact"],
                "instrumentIds": data["instrumentIds"],
                "instrumentNames": data.get("instrumentNames", ""),
                "instrumentQuantities": quantities,
                "startTime": data["startTime"],
                "endTime": data["endTime"],
                "purpose": data["purpose"],
                "notes": data.get("notes", ""),
            }

            # 更新仪器状态
            for inst_id in data["instrumentIds"]:
                inst = next((i for i in instruments if i["id"] == inst_id), None)
                if inst:
                    requested_qty = quantities.get(str(inst_id), 1)
                    inst["available"] = (
                        inst.get("available", inst["quantity"]) - requested_qty
                    )
                    if inst["available"] <= 0:
                        inst["status"] = "inuse"
                    elif inst["available"] < inst["quantity"] * 0.3:
                        inst["status"] = "limited"
                    else:
                        inst["status"] = "available"
                    if "currentUsers" not in inst:
                        inst["currentUsers"] = []
                    # 添加多次用户名（表示借用多台）
                    for _ in range(requested_qty):
                        inst["currentUsers"].append(data["userName"])

            # 保存数据
            records.append(record)
            history.append(record)

            save_instruments(instruments)
            save_records(records)
            save_history(history)

            # 备份数据
            backup_data()

            self.send_json_response({"success": True, "data": record})

        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)})

    def handle_release(self):
        """处理释放仪器请求"""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode("utf-8"))
            record_id = data.get("recordId")

            if not record_id:
                self.send_json_response({"success": False, "error": "缺少记录ID"})
                return

            instruments, records, _ = load_data()

            # 找到记录
            record = next((r for r in records if r["id"] == record_id), None)
            if not record:
                self.send_json_response({"success": False, "error": "记录不存在"})
                return

            # 释放仪器
            quantities = record.get("instrumentQuantities", {})
            for inst_id in record["instrumentIds"]:
                inst = next((i for i in instruments if i["id"] == inst_id), None)
                if inst:
                    # 获取归还数量（兼容旧记录）
                    return_qty = quantities.get(str(inst_id), 1)
                    inst["available"] = min(
                        inst.get("available", 0) + return_qty, inst["quantity"]
                    )
                    if inst["available"] >= inst["quantity"]:
                        inst["status"] = "available"
                    elif inst["available"] < inst["quantity"] * 0.3:
                        inst["status"] = "limited"
                    else:
                        inst["status"] = "available"
                    # 移除对应次数的用户名
                    if record["userName"] in inst.get("currentUsers", []):
                        for _ in range(return_qty):
                            if record["userName"] in inst["currentUsers"]:
                                inst["currentUsers"].remove(record["userName"])

            # 更新记录结束时间
            record["endTime"] = datetime.now(timezone.utc).isoformat()

            save_instruments(instruments)
            save_records(records)

            self.send_json_response({"success": True})

        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)})

    def log_message(self, format, *args):
        """自定义日志"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}")


def run_server(port=8081):
    """运行HTTP服务器"""
    server = HTTPServer(("127.0.0.1", port), APIHandler)
    print(f"🚀 服务器已启动!")
    print(f"🌐 请打开浏览器访问: http://127.0.0.1:{port}")
    print(f"📁 数据目录: {DATA_DIR}")
    print(f"💾 备份目录: {BACKUP_DIR}")
    print(f"\n按 Ctrl+C 停止服务器")
    print("=" * 50)
    server.serve_forever()


def scheduled_tasks():
    """定时任务"""
    while True:
        now = datetime.now()

        # 每分钟检查一次仪器状态
        check_and_update_status()

        # 每天凌晨备份数据
        if now.hour == 0 and now.minute == 0:
            backup_data()
            print(f"✅ [{now.strftime('%Y-%m-%d %H:%M:%S')}] 每日自动备份完成")

        time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    # 初始化数据
    load_data()

    # 启动定时任务线程
    task_thread = threading.Thread(target=scheduled_tasks, daemon=True)
    task_thread.start()

    # 启动服务器
    run_server()

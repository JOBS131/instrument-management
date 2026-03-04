#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪器设备管理系统 - Flask版本
支持部署到Render等云平台
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

# 数据存储路径
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

INSTRUMENTS_FILE = DATA_DIR / "instruments.json"
RECORDS_FILE = DATA_DIR / "records.json"
HISTORY_FILE = DATA_DIR / "history.json"


def load_data():
    """加载数据"""
    instruments = []
    records = []
    history = []

    if INSTRUMENTS_FILE.exists():
        with open(INSTRUMENTS_FILE, "r", encoding="utf-8") as f:
            instruments = json.load(f)

    if RECORDS_FILE.exists():
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)

    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    return instruments, records, history


def save_instruments(instruments):
    with open(INSTRUMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(instruments, f, ensure_ascii=False, indent=2)


def save_records(records):
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/instruments')
def get_instruments():
    instruments, _, _ = load_data()
    return jsonify({"success": True, "data": instruments})


@app.route('/api/records')
def get_records():
    _, records, _ = load_data()
    now = datetime.now(timezone.utc)
    active_records = []
    
    for r in records:
        try:
            end_time_str = r["endTime"]
            if "+" in end_time_str or "Z" in end_time_str:
                end_time_str = end_time_str.replace("Z", "+00:00")
                end_time = datetime.fromisoformat(end_time_str)
            else:
                end_time = datetime.fromisoformat(end_time_str)
                end_time = end_time.replace(tzinfo=timezone.utc) - timedelta(hours=8)
            
            if end_time > now:
                active_records.append(r)
        except:
            pass
    
    return jsonify({"success": True, "data": active_records})


@app.route('/api/history')
def get_history():
    _, _, history = load_data()
    return jsonify({"success": True, "data": history[-100:]})


@app.route('/api/stats')
def get_stats():
    instruments, _, _ = load_data()
    total = sum(i["quantity"] for i in instruments)
    available = sum(i.get("available", 0) for i in instruments)
    in_use = total - available
    return jsonify({"success": True, "data": {"total": total, "available": available, "inUse": in_use}})


@app.route('/api/register', methods=['POST'])
def handle_register():
    try:
        data = request.get_json()
        instruments, records, history = load_data()
        
        quantities = data.get("instrumentQuantities", {})
        if not quantities:
            quantities = {str(inst_id): 1 for inst_id in data["instrumentIds"]}
        
        # 检查仪器
        for inst_id in data["instrumentIds"]:
            inst = next((i for i in instruments if i["id"] == inst_id), None)
            if not inst:
                return jsonify({"success": False, "error": f"仪器不存在: ID {inst_id}"})
            
            requested_qty = quantities.get(str(inst_id), 1)
            available_qty = inst.get("available", inst.get("quantity", 0))
            
            if available_qty < requested_qty:
                return jsonify({"success": False, 
                    "error": f"仪器 {inst['name']} 可用数量不足，仅剩 {available_qty} 台"})
        
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
                inst["available"] = inst.get("available", inst["quantity"]) - requested_qty
                if inst["available"] <= 0:
                    inst["status"] = "inuse"
                elif inst["available"] < inst["quantity"] * 0.3:
                    inst["status"] = "limited"
                else:
                    inst["status"] = "available"
                if "currentUsers" not in inst:
                    inst["currentUsers"] = []
                for _ in range(requested_qty):
                    inst["currentUsers"].append(data["userName"])
        
        records.append(record)
        history.append(record)
        
        save_instruments(instruments)
        save_records(records)
        save_history(history)
        
        return jsonify({"success": True, "data": record})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/release', methods=['POST'])
def handle_release():
    try:
        data = request.get_json()
        record_id = data.get("recordId")
        
        if not record_id:
            return jsonify({"success": False, "error": "缺少记录ID"})
        
        instruments, records, _ = load_data()
        
        record = next((r for r in records if r["id"] == record_id), None)
        if not record:
            return jsonify({"success": False, "error": "记录不存在"})
        
        quantities = record.get("instrumentQuantities", {})
        for inst_id in record["instrumentIds"]:
            inst = next((i for i in instruments if i["id"] == inst_id), None)
            if inst:
                return_qty = quantities.get(str(inst_id), 1)
                inst["available"] = min(inst.get("available", 0) + return_qty, inst["quantity"])
                if inst["available"] >= inst["quantity"]:
                    inst["status"] = "available"
                elif inst["available"] < inst["quantity"] * 0.3:
                    inst["status"] = "limited"
                else:
                    inst["status"] = "available"
                if record["userName"] in inst.get("currentUsers", []):
                    for _ in range(return_qty):
                        if record["userName"] in inst["currentUsers"]:
                            inst["currentUsers"].remove(record["userName"])
        
        record["endTime"] = datetime.now(timezone.utc).isoformat()
        
        save_instruments(instruments)
        save_records(records)
        
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port, debug=True)

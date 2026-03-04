#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪器设备管理系统 - Flask版本（带用户认证和审批）
"""

import json
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
app.secret_key = "your-secret-key-change-in-production"
CORS(app, supports_credentials=True)

# 数据存储路径
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

INSTRUMENTS_FILE = DATA_DIR / "instruments.json"
RECORDS_FILE = DATA_DIR / "records.json"
HISTORY_FILE = DATA_DIR / "history.json"
USERS_FILE = DATA_DIR / "users.json"
PENDING_FILE = DATA_DIR / "pending.json"


def load_data():
    """加载数据"""
    instruments = []
    records = []
    history = []
    users = []
    pending = []

    if INSTRUMENTS_FILE.exists():
        with open(INSTRUMENTS_FILE, "r", encoding="utf-8") as f:
            instruments = json.load(f)

    if RECORDS_FILE.exists():
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)

    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)

    if PENDING_FILE.exists():
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            pending = json.load(f)

    return instruments, records, history, users, pending


def save_json(data, filepath):
    """保存JSON文件"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def require_auth(f):
    """需要登录的装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "error": "请先登录"}), 401
        return f(*args, **kwargs)

    return decorated_function


def require_admin(f):
    """需要管理员权限的装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "error": "请先登录"}), 401

        _, _, _, users, _ = load_data()
        user = next((u for u in users if u["id"] == session["user_id"]), None)
        if not user or user.get("role") != "admin":
            return jsonify({"success": False, "error": "需要管理员权限"}), 403
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    return send_from_directory(".", "login.html")


@app.route("/login.html")
def login_page():
    return send_from_directory(".", "login.html")


@app.route("/index_new.html")
def main_page():
    return send_from_directory(".", "index_new.html")


@app.route("/index.html")
def old_index():
    return send_from_directory(".", "index.html")


# ==================== 用户认证 API ====================


@app.route("/api/auth/login", methods=["POST"])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "error": "请输入用户名和密码"})

    _, _, _, users, _ = load_data()
    password_hash = hash_password(password)

    user = next(
        (
            u
            for u in users
            if u["username"] == username and u["password_hash"] == password_hash
        ),
        None,
    )

    if not user:
        return jsonify({"success": False, "error": "用户名或密码错误"})

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user.get("role", "user")

    return jsonify(
        {
            "success": True,
            "data": {
                "id": user["id"],
                "username": user["username"],
                "name": user["name"],
                "role": user.get("role", "user"),
            },
        }
    )


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    """用户登出"""
    session.clear()
    return jsonify({"success": True})


@app.route("/api/auth/me", methods=["GET"])
def get_current_user():
    """获取当前登录用户"""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "未登录"})

    _, _, _, users, _ = load_data()
    user = next((u for u in users if u["id"] == session["user_id"]), None)

    if not user:
        session.clear()
        return jsonify({"success": False, "error": "用户不存在"})

    return jsonify(
        {
            "success": True,
            "data": {
                "id": user["id"],
                "username": user["username"],
                "name": user["name"],
                "role": user.get("role", "user"),
            },
        }
    )


@app.route("/api/auth/register", methods=["POST"])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    name = data.get("name", "").strip()

    if not username or not password or not name:
        return jsonify({"success": False, "error": "请填写完整信息"})

    _, _, _, users, _ = load_data()

    # 检查用户名是否已存在
    if any(u["username"] == username for u in users):
        return jsonify({"success": False, "error": "用户名已存在"})

    # 创建新用户（普通用户角色）
    new_user = {
        "id": int(datetime.now(timezone.utc).timestamp() * 1000),
        "username": username,
        "password_hash": hash_password(password),
        "name": name,
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    users.append(new_user)
    save_json(users, USERS_FILE)

    return jsonify({"success": True, "message": "注册成功，请登录"})


# ==================== 仪器管理 API ====================


@app.route("/api/instruments")
def get_instruments():
    """获取仪器列表"""
    instruments, _, _, _, _ = load_data()
    return jsonify({"success": True, "data": instruments})


@app.route("/api/stats")
def get_stats():
    """获取统计信息"""
    instruments, _, _, _, _ = load_data()
    total = sum(i["quantity"] for i in instruments)
    available = sum(i.get("available", 0) for i in instruments)
    in_use = total - available

    return jsonify(
        {
            "success": True,
            "data": {"total": total, "available": available, "inUse": in_use},
        }
    )


# ==================== 审批系统 API ====================


@app.route("/api/borrow/apply", methods=["POST"])
@require_auth
def apply_borrow():
    """提交借用申请"""
    try:
        data = request.get_json()
        user_id = session["user_id"]
        username = session["username"]

        instruments, _, _, _, pending = load_data()

        # 获取数量信息
        quantities = data.get("instrumentQuantities", {})
        if not quantities:
            quantities = {str(inst_id): 1 for inst_id in data["instrumentIds"]}

        # 检查仪器可用性
        for inst_id in data["instrumentIds"]:
            inst = next((i for i in instruments if i["id"] == inst_id), None)
            if not inst:
                return jsonify({"success": False, "error": f"仪器不存在: ID {inst_id}"})

            requested_qty = quantities.get(str(inst_id), 1)
            available_qty = inst.get("available", inst.get("quantity", 0))

            if available_qty < requested_qty:
                return jsonify(
                    {
                        "success": False,
                        "error": f"仪器 {inst['name']} 可用数量不足，仅剩 {available_qty} 台",
                    }
                )

        # 创建申请记录
        application = {
            "id": int(datetime.now(timezone.utc).timestamp() * 1000),
            "userId": user_id,
            "userName": username,
            "userDept": data.get("userDept", ""),
            "userContact": data.get("userContact", ""),
            "instrumentIds": data["instrumentIds"],
            "instrumentNames": data.get("instrumentNames", ""),
            "instrumentQuantities": quantities,
            "startTime": data["startTime"],
            "endTime": data["endTime"],
            "purpose": data["purpose"],
            "notes": data.get("notes", ""),
            "status": "pending",
            "applyTime": datetime.now(timezone.utc).isoformat(),
            "reviewTime": None,
            "reviewerId": None,
            "reviewerName": None,
            "rejectReason": None,
        }

        pending.append(application)
        save_json(pending, PENDING_FILE)

        return jsonify(
            {
                "success": True,
                "data": application,
                "message": "申请已提交，等待管理员审批",
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/borrow/pending", methods=["GET"])
@require_auth
def get_pending_applications():
    """获取待审批列表"""
    _, _, _, _, pending = load_data()
    role = session.get("role", "user")
    user_id = session["user_id"]

    if role == "admin":
        # 管理员看所有待审批
        applications = [p for p in pending if p["status"] == "pending"]
    else:
        # 普通用户只看自己的
        applications = [p for p in pending if p["userId"] == user_id]

    return jsonify({"success": True, "data": applications})


@app.route("/api/borrow/review", methods=["POST"])
@require_admin
def review_application():
    """审批借用申请（仅管理员）"""
    try:
        data = request.get_json()
        application_id = data.get("applicationId")
        action = data.get("action")
        reason = data.get("reason", "")

        if not application_id or action not in ["approve", "reject"]:
            return jsonify({"success": False, "error": "参数错误"})

        instruments, records, history, _, pending = load_data()

        application = next((p for p in pending if p["id"] == application_id), None)
        if not application:
            return jsonify({"success": False, "error": "申请不存在"})

        if application["status"] != "pending":
            return jsonify({"success": False, "error": "该申请已处理"})

        reviewer_id = session["user_id"]
        reviewer_name = session.get("username", "管理员")

        if action == "approve":
            # 批准申请
            quantities = application.get("instrumentQuantities", {})

            # 扣减库存
            for inst_id in application["instrumentIds"]:
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
                    if "currentUsers" not in inst:
                        inst["currentUsers"] = []
                    for _ in range(requested_qty):
                        inst["currentUsers"].append(application["userName"])

            # 创建正式借用记录
            record = {
                "id": application["id"],
                "registerTime": datetime.now(timezone.utc).isoformat(),
                "userId": application["userId"],
                "userName": application["userName"],
                "userDept": application["userDept"],
                "userContact": application["userContact"],
                "instrumentIds": application["instrumentIds"],
                "instrumentNames": application["instrumentNames"],
                "instrumentQuantities": quantities,
                "startTime": application["startTime"],
                "endTime": application["endTime"],
                "purpose": application["purpose"],
                "notes": application["notes"],
                "approvedBy": reviewer_name,
                "approvedTime": datetime.now(timezone.utc).isoformat(),
            }

            records.append(record)
            history.append(record)

            save_json(instruments, INSTRUMENTS_FILE)
            save_json(records, RECORDS_FILE)
            save_json(history, HISTORY_FILE)

            application["status"] = "approved"
            application["reviewTime"] = datetime.now(timezone.utc).isoformat()
            application["reviewerId"] = reviewer_id
            application["reviewerName"] = reviewer_name

            save_json(pending, PENDING_FILE)

            return jsonify({"success": True, "message": "申请已通过"})

        else:  # reject
            application["status"] = "rejected"
            application["reviewTime"] = datetime.now(timezone.utc).isoformat()
            application["reviewerId"] = reviewer_id
            application["reviewerName"] = reviewer_name
            application["rejectReason"] = reason

            save_json(pending, PENDING_FILE)

            return jsonify({"success": True, "message": "申请已拒绝"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ==================== 记录查询 API ====================


@app.route("/api/records")
def get_records():
    """获取当前借用记录（公开访问，不显示敏感信息）"""
    _, records, _, _, _ = load_data()
    now = datetime.now(timezone.utc)

    # 检查是否登录
    is_logged_in = "user_id" in session
    role = session.get("role", "user") if is_logged_in else "guest"
    user_id = session.get("user_id") if is_logged_in else None

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
                # 未登录用户只能看概览，登录用户看自己的，管理员看所有
                if role == "admin":
                    active_records.append(r)
                elif is_logged_in and r.get("userId") == user_id:
                    active_records.append(r)
                else:
                    # 未登录用户看到的是简化信息
                    simplified = {
                        "id": r["id"],
                        "userName": r["userName"],
                        "instrumentNames": r["instrumentNames"],
                        "registerTime": r["registerTime"],
                    }
                    active_records.append(simplified)
        except:
            pass

    return jsonify({"success": True, "data": active_records})


@app.route("/api/history")
def get_history():
    """获取历史记录（公开访问）"""
    _, _, history, _, _ = load_data()

    # 检查是否登录
    is_logged_in = "user_id" in session
    role = session.get("role", "user") if is_logged_in else "guest"
    user_id = session.get("user_id") if is_logged_in else None

    if role == "admin":
        filtered_history = history[-100:]
    elif is_logged_in:
        filtered_history = [h for h in history if h.get("userId") == user_id][-100:]
    else:
        # 未登录用户看到简化的历史记录
        filtered_history = [
            {
                "id": h["id"],
                "userName": h["userName"],
                "instrumentNames": h["instrumentNames"],
                "registerTime": h["registerTime"],
            }
            for h in history[-50:]
        ]

    return jsonify({"success": True, "data": filtered_history})


# ==================== 归还 API ====================


@app.route("/api/return", methods=["POST"])
@require_auth
def return_instruments():
    """归还仪器"""
    try:
        data = request.get_json()
        record_id = data.get("recordId")
        user_id = session["user_id"]
        role = session.get("role", "user")

        if not record_id:
            return jsonify({"success": False, "error": "缺少记录ID"})

        instruments, records, _, _, _ = load_data()

        record = next((r for r in records if r["id"] == record_id), None)
        if not record:
            return jsonify({"success": False, "error": "记录不存在"})

        # 权限检查
        if role != "admin" and record.get("userId") != user_id:
            return jsonify({"success": False, "error": "只能归还自己借用的设备"})

        # 归还仪器
        quantities = record.get("instrumentQuantities", {})
        for inst_id in record["instrumentIds"]:
            inst = next((i for i in instruments if i["id"] == inst_id), None)
            if inst:
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

                if record["userName"] in inst.get("currentUsers", []):
                    for _ in range(return_qty):
                        if record["userName"] in inst["currentUsers"]:
                            inst["currentUsers"].remove(record["userName"])

        record["endTime"] = datetime.now(timezone.utc).isoformat()
        record["returnedBy"] = session.get("username", "未知")
        record["returnTime"] = datetime.now(timezone.utc).isoformat()

        save_json(instruments, INSTRUMENTS_FILE)
        save_json(records, RECORDS_FILE)

        return jsonify({"success": True, "message": "归还成功"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ==================== 管理员 API ====================


@app.route("/api/admin/users", methods=["GET"])
@require_admin
def get_all_users():
    """获取所有用户（仅管理员）"""
    _, _, _, users, _ = load_data()
    safe_users = [{k: v for k, v in u.items() if k != "password_hash"} for u in users]
    return jsonify({"success": True, "data": safe_users})


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 8081))
    app.run(host="0.0.0.0", port=port, debug=True)

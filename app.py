#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪器设备管理系统 - Flask版本（带用户认证和审批）
使用Token认证替代Session
"""

import json
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
app.secret_key = "instrument-management-system-secret-key-2024"

# CORS配置 - 允许所有来源
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-User-ID", "X-User-Role"],
        }
    },
)

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


def get_current_user():
    """从session获取当前用户"""
    user_id = session.get("user_id")

    if not user_id:
        return None

    _, _, _, users, _ = load_data()
    user = next((u for u in users if u["id"] == user_id), None)

    if user:
        return {
            "id": user["id"],
            "username": user["username"],
            "name": user["name"],
            "role": user.get("role", "user"),
            "status": user.get("status", "approved"),
        }
    return None


def require_auth(f):
    """需要登录的装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "请先登录"}), 401
        if user.get("status") == "pending":
            return jsonify(
                {"success": False, "error": "账号正在审批中，请等待管理员审核"}
            ), 403
        if user.get("status") == "rejected":
            return jsonify(
                {"success": False, "error": "账号已被拒绝，请联系管理员"}
            ), 403
        return f(*args, **kwargs)

    return decorated_function


def require_admin(f):
    """需要管理员权限的装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "请先登录"}), 401
        if user.get("role") != "admin":
            return jsonify({"success": False, "error": "需要管理员权限"}), 403
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    """主页 - 重定向到登录页"""
    return send_from_directory(".", "login.html")


@app.route("/login.html")
def login_page():
    """登录页面"""
    return send_from_directory(".", "login.html")


@app.route("/logo.png")
def logo():
    """Logo图片"""
    return send_from_directory(".", "澳大河套集成电路研究院.png")


@app.route("/index_new.html")
def main_page():
    """仪器管理主页面 - 需要登录"""
    user = get_current_user()
    if not user:
        # 未登录，返回需要登录的提示或重定向脚本
        return (
            """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>需要登录</title>
    <script>
        window.location.href = '/login.html';
    </script>
</head>
<body>
    <p>请先登录，正在跳转到登录页面...</p>
</body>
</html>""",
            401,
        )
    return send_from_directory(".", "index_new.html")


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

    if user.get("status") == "pending":
        return jsonify({"success": False, "error": "账号正在审批中，请等待管理员审核"})

    if user.get("status") == "rejected":
        return jsonify({"success": False, "error": "账号已被拒绝，请联系管理员"})

    if user.get("status") == "locked":
        return jsonify({"success": False, "error": "账号已被锁定，请联系管理员解锁"})

    # 设置session
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
def get_current_user_info():
    """获取当前登录用户"""
    user = get_current_user()

    if not user:
        return jsonify({"success": False, "error": "未登录"})

    return jsonify({"success": True, "data": user})


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

    # 创建新用户（普通用户角色，状态为待审批）
    new_user = {
        "id": int(datetime.now(timezone.utc).timestamp() * 1000),
        "username": username,
        "password_hash": hash_password(password),
        "name": name,
        "role": "user",
        "status": "pending",  # pending, approved, rejected
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    users.append(new_user)
    save_json(users, USERS_FILE)

    return jsonify({"success": True, "message": "注册成功，请等待管理员审批"})


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
        user = get_current_user()

        if not user:
            return jsonify({"success": False, "error": "请先登录"})

        user_id = user["id"]
        username = user["username"]

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
            "purpose": data.get("purpose", ""),
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
    user = get_current_user()

    if not user:
        return jsonify({"success": False, "error": "请先登录"})

    role = user.get("role", "user")
    user_id = user["id"]

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

        reviewer = get_current_user()
        reviewer_id = reviewer["id"]
        reviewer_name = reviewer.get("username", "管理员")

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
    user = get_current_user()
    is_logged_in = user is not None
    role = user.get("role", "guest") if user else "guest"
    user_id = user.get("id") if user else None

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

    user = get_current_user()
    is_logged_in = user is not None
    role = user.get("role", "guest") if user else "guest"
    user_id = user.get("id") if user else None

    if role == "admin":
        filtered_history = history[-100:]
    elif is_logged_in:
        filtered_history = [h for h in history if h.get("userId") == user_id][-100:]
    else:
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
    """归还仪器 - 支持单独归还某个仪器"""
    try:
        data = request.get_json()
        record_id = data.get("recordId")
        instrument_id = data.get("instrumentId")  # 可选，如果指定则只归还该仪器

        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "请先登录"})

        user_id = user["id"]
        role = user.get("role", "user")

        if not record_id:
            return jsonify({"success": False, "error": "缺少记录ID"})

        instruments, records, _, _, _ = load_data()

        record = next((r for r in records if r["id"] == record_id), None)
        if not record:
            return jsonify({"success": False, "error": "记录不存在"})

        # 权限检查
        if role != "admin" and record.get("userId") != user_id:
            return jsonify({"success": False, "error": "只能归还自己借用的设备"})

        # 确定要归还的仪器列表
        quantities = record.get("instrumentQuantities", {})
        message = "归还成功"  # 默认消息
        if instrument_id:
            # 只归还指定仪器
            inst_ids_to_return = [int(instrument_id)]
        else:
            # 归还所有仪器
            inst_ids_to_return = record["instrumentIds"]

        # 归还仪器
        for inst_id in inst_ids_to_return:
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

        if instrument_id:
            # 部分归还：从记录中移除该仪器
            inst_id_int = int(instrument_id)
            if inst_id_int in record["instrumentIds"]:
                record["instrumentIds"].remove(inst_id_int)
                if str(inst_id_int) in record.get("instrumentQuantities", {}):
                    del record["instrumentQuantities"][str(inst_id_int)]
                # 更新仪器名称列表
                record["instrumentNames"] = ", ".join(
                    [
                        f"{next((i['name'] for i in instruments if i['id'] == iid), '未知')}({next((i['model'] for i in instruments if i['id'] == iid), '-')}) x{quantities.get(str(iid), 1)}台"
                        for iid in record["instrumentIds"]
                    ]
                )

                # 如果所有仪器都已归还，删除记录
                if len(record["instrumentIds"]) == 0:
                    records.remove(record)
                    message = "归还成功，所有仪器已归还"
                else:
                    message = "归还成功"
        else:
            # 全部归还
            record["endTime"] = datetime.now(timezone.utc).isoformat()
            record["returnedBy"] = user.get("username", "未知")
            record["returnTime"] = datetime.now(timezone.utc).isoformat()
            message = "归还成功"

        save_json(instruments, INSTRUMENTS_FILE)
        save_json(records, RECORDS_FILE)

        return jsonify({"success": True, "message": message})

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


@app.route("/api/admin/users/pending", methods=["GET"])
@require_admin
def get_pending_users():
    """获取待审批用户列表（仅管理员）"""
    _, _, _, users, _ = load_data()
    pending_users = [u for u in users if u.get("status") == "pending"]
    safe_users = [
        {k: v for k, v in u.items() if k != "password_hash"} for u in pending_users
    ]
    return jsonify({"success": True, "data": safe_users})


@app.route("/api/admin/users/review", methods=["POST"])
@require_admin
def review_user():
    """审批用户注册（仅管理员）"""
    try:
        data = request.get_json()
        user_id = data.get("userId")
        action = data.get("action")  # 'approve' 或 'reject'

        if not user_id or action not in ["approve", "reject"]:
            return jsonify({"success": False, "error": "参数错误"})

        _, _, _, users, _ = load_data()

        user = next((u for u in users if u["id"] == user_id), None)
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})

        if user.get("status") != "pending":
            return jsonify({"success": False, "error": "该用户已处理"})

        if action == "approve":
            user["status"] = "approved"
            message = "用户已通过审批"
        else:
            user["status"] = "rejected"
            message = "用户已被拒绝"

        save_json(users, USERS_FILE)

        return jsonify({"success": True, "message": message})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/admin/users/lock", methods=["POST"])
@require_admin
def lock_user():
    """锁定/解锁用户账户（仅管理员）"""
    try:
        data = request.get_json()
        user_id = data.get("userId")
        action = data.get("action")  # 'lock' 或 'unlock'

        if not user_id or action not in ["lock", "unlock"]:
            return jsonify({"success": False, "error": "参数错误"})

        _, _, _, users, _ = load_data()

        user = next((u for u in users if u["id"] == user_id), None)
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})

        if user.get("role") == "admin":
            return jsonify({"success": False, "error": "不能锁定管理员账户"})

        if action == "lock":
            user["status"] = "locked"
            message = "用户账户已锁定"
        else:
            user["status"] = "approved"
            message = "用户账户已解锁"

        save_json(users, USERS_FILE)

        return jsonify({"success": True, "message": message})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/admin/users/delete", methods=["POST"])
@require_admin
def delete_user():
    """注销/删除用户账户（仅管理员）"""
    try:
        data = request.get_json()
        user_id = data.get("userId")

        if not user_id:
            return jsonify({"success": False, "error": "参数错误"})

        _, _, _, users, _ = load_data()

        user = next((u for u in users if u["id"] == user_id), None)
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})

        if user.get("role") == "admin":
            return jsonify({"success": False, "error": "不能注销管理员账户"})

        # 从列表中移除用户
        users.remove(user)

        save_json(users, USERS_FILE)

        return jsonify({"success": True, "message": "用户账户已注销"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 8081))
    app.run(host="0.0.0.0", port=port, debug=True)

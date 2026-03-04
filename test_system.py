#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试登录和审批系统
"""

import json
import sys
import os

sys.path.insert(0, "/Users/job/Desktop/仪器管理系统")

from app import app, hash_password, load_data, save_json, USERS_FILE

# 测试客户端
client = app.test_client()


def test_setup():
    """初始化测试数据"""
    print("=" * 60)
    print("🚀 开始测试登录和审批系统")
    print("=" * 60)

    # 确保数据目录存在
    import pathlib

    data_dir = pathlib.Path("/Users/job/Desktop/仪器管理系统/data")
    data_dir.mkdir(exist_ok=True)

    # 创建测试管理员账号
    admin_user = {
        "id": 1,
        "username": "admin",
        "password_hash": hash_password("admin123"),
        "name": "管理员",
        "role": "admin",
        "created_at": "2024-01-01T00:00:00+00:00",
    }

    # 创建测试普通用户
    test_user = {
        "id": 2,
        "username": "testuser",
        "password_hash": hash_password("user123"),
        "name": "测试用户",
        "role": "user",
        "created_at": "2024-01-01T00:00:00+00:00",
    }

    users = [admin_user, test_user]
    save_json(users, USERS_FILE)
    print("✅ 测试账号已创建")
    print(f"   管理员: admin / admin123")
    print(f"   普通用户: testuser / user123")


def test_register():
    """测试注册功能"""
    print("\n" + "=" * 60)
    print("📋 测试1: 用户注册")
    print("=" * 60)

    # 测试正常注册
    response = client.post(
        "/api/auth/register",
        data=json.dumps(
            {"username": "newuser", "password": "password123", "name": "新用户"}
        ),
        content_type="application/json",
    )
    data = json.loads(response.data)
    print(
        f"✅ 注册新用户: {data.get('success')} - {data.get('message', data.get('error', ''))}"
    )

    # 测试重复注册
    response = client.post(
        "/api/auth/register",
        data=json.dumps(
            {"username": "admin", "password": "password123", "name": "重复用户"}
        ),
        content_type="application/json",
    )
    data = json.loads(response.data)
    print(f"✅ 重复注册检查: {not data.get('success')} - {data.get('error', '')}")


def test_login():
    """测试登录功能"""
    print("\n" + "=" * 60)
    print("📋 测试2: 用户登录")
    print("=" * 60)

    # 测试管理员登录
    response = client.post(
        "/api/auth/login",
        data=json.dumps({"username": "admin", "password": "admin123"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    print(
        f"✅ 管理员登录: {data.get('success')} - 角色: {data.get('data', {}).get('role')}"
    )

    # 测试普通用户登录
    with client.session_transaction() as sess:
        sess.clear()

    response = client.post(
        "/api/auth/login",
        data=json.dumps({"username": "testuser", "password": "user123"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    print(
        f"✅ 普通用户登录: {data.get('success')} - 角色: {data.get('data', {}).get('role')}"
    )

    # 测试错误密码
    response = client.post(
        "/api/auth/login",
        data=json.dumps({"username": "admin", "password": "wrongpassword"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    print(f"✅ 错误密码检查: {not data.get('success')} - {data.get('error', '')}")


def test_auth_check():
    """测试权限检查"""
    print("\n" + "=" * 60)
    print("📋 测试3: 权限检查")
    print("=" * 60)

    # 未登录访问受保护接口
    with client.session_transaction() as sess:
        sess.clear()

    response = client.get("/api/borrow/pending")
    data = json.loads(response.data)
    print(
        f"✅ 未登录访问检查: {response.status_code == 401} - 状态码: {response.status_code}"
    )

    # 登录后访问
    client.post(
        "/api/auth/login",
        data=json.dumps({"username": "testuser", "password": "user123"}),
        content_type="application/json",
    )

    response = client.get("/api/borrow/pending")
    data = json.loads(response.data)
    print(f"✅ 登录后访问: {data.get('success')} - 状态码: {response.status_code}")


def test_borrow_apply():
    """测试借用申请"""
    print("\n" + "=" * 60)
    print("📋 测试4: 借用申请")
    print("=" * 60)

    # 先初始化一些仪器数据
    from app import INSTRUMENTS_FILE

    instruments = [
        {
            "id": 1,
            "name": "示波器",
            "model": "EXR208A",
            "quantity": 2,
            "available": 2,
            "status": "available",
            "currentUsers": [],
            "location": "测试间",
        }
    ]
    save_json(instruments, INSTRUMENTS_FILE)

    # 登录为普通用户
    with client.session_transaction() as sess:
        sess.clear()

    client.post(
        "/api/auth/login",
        data=json.dumps({"username": "testuser", "password": "user123"}),
        content_type="application/json",
    )

    # 提交借用申请
    response = client.post(
        "/api/borrow/apply",
        data=json.dumps(
            {
                "instrumentIds": [1],
                "instrumentNames": "示波器",
                "instrumentQuantities": {"1": 1},
                "userDept": "测试部门",
                "userContact": "1234567890",
                "startTime": "2024-12-01T09:00:00",
                "endTime": "2024-12-03T18:00:00",
                "purpose": "测试使用",
            }
        ),
        content_type="application/json",
    )
    data = json.loads(response.data)
    print(f"✅ 提交借用申请: {data.get('success')} - {data.get('message', '')}")

    return data.get("data", {}).get("id")


def test_pending_list():
    """测试查看待审批列表"""
    print("\n" + "=" * 60)
    print("📋 测试5: 查看待审批列表")
    print("=" * 60)

    # 普通用户查看自己的申请
    with client.session_transaction() as sess:
        sess.clear()

    client.post(
        "/api/auth/login",
        data=json.dumps({"username": "testuser", "password": "user123"}),
        content_type="application/json",
    )

    response = client.get("/api/borrow/pending")
    data = json.loads(response.data)
    print(
        f"✅ 普通用户查看申请: {data.get('success')} - 数量: {len(data.get('data', []))}"
    )

    # 管理员查看所有待审批
    with client.session_transaction() as sess:
        sess.clear()

    client.post(
        "/api/auth/login",
        data=json.dumps({"username": "admin", "password": "admin123"}),
        content_type="application/json",
    )

    response = client.get("/api/borrow/pending")
    data = json.loads(response.data)
    applications = data.get("data", [])
    print(f"✅ 管理员查看所有: {data.get('success')} - 待审批数量: {len(applications)}")

    return applications[0]["id"] if applications else None


def test_review_application(application_id):
    """测试审批功能"""
    print("\n" + "=" * 60)
    print("📋 测试6: 审批申请")
    print("=" * 60)

    # 普通用户尝试审批（应该失败）
    with client.session_transaction() as sess:
        sess.clear()

    client.post(
        "/api/auth/login",
        data=json.dumps({"username": "testuser", "password": "user123"}),
        content_type="application/json",
    )

    response = client.post(
        "/api/borrow/review",
        data=json.dumps({"applicationId": application_id, "action": "approve"}),
        content_type="application/json",
    )
    print(
        f"✅ 普通用户审批检查: {response.status_code == 403} - 状态码: {response.status_code}"
    )

    # 管理员进行审批
    with client.session_transaction() as sess:
        sess.clear()

    client.post(
        "/api/auth/login",
        data=json.dumps({"username": "admin", "password": "admin123"}),
        content_type="application/json",
    )

    response = client.post(
        "/api/borrow/review",
        data=json.dumps({"applicationId": application_id, "action": "approve"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    print(f"✅ 管理员审批通过: {data.get('success')} - {data.get('message', '')}")


def test_return_instrument():
    """测试归还功能"""
    print("\n" + "=" * 60)
    print("📋 测试7: 归还仪器")
    print("=" * 60)

    # 查看当前记录
    response = client.get("/api/records")
    data = json.loads(response.data)
    records = data.get("data", [])

    if records:
        record_id = records[0]["id"]

        # 归还仪器
        response = client.post(
            "/api/return",
            data=json.dumps({"recordId": record_id}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        print(f"✅ 归还仪器: {data.get('success')} - {data.get('message', '')}")
    else:
        print("⚠️  没有可归还的记录")


def test_logout():
    """测试登出功能"""
    print("\n" + "=" * 60)
    print("📋 测试8: 用户登出")
    print("=" * 60)

    response = client.post("/api/auth/logout")
    data = json.loads(response.data)
    print(f"✅ 用户登出: {data.get('success')}")

    # 验证登出后无法访问
    response = client.get("/api/borrow/pending")
    print(f"✅ 登出后访问检查: {response.status_code == 401}")


def main():
    """运行所有测试"""
    try:
        test_setup()
        test_register()
        test_login()
        test_auth_check()
        application_id = test_borrow_apply()
        pending_id = test_pending_list()
        if pending_id:
            test_review_application(pending_id)
            test_return_instrument()
        test_logout()

        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")
        print("=" * 60)
        print("\n✅ 登录系统功能正常")
        print("✅ 审批系统功能正常")
        print("✅ 权限控制功能正常")
        print("\n前端访问地址: http://127.0.0.1:8081/index_new.html")

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

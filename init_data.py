#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化仪器管理系统数据
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def init_users():
    """初始化用户数据"""
    users_file = DATA_DIR / "users.json"

    users = [
        {
            "id": 1,
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "name": "管理员",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": 2,
            "username": "testuser",
            "password_hash": hash_password("user123"),
            "name": "测试用户",
            "role": "user",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

    print(f"✅ 用户数据已初始化: {users_file}")
    print(f"   管理员: admin / admin123")
    print(f"   普通用户: testuser / user123")


def init_instruments():
    """初始化仪器数据"""
    instruments_file = DATA_DIR / "instruments.json"

    # 如果已存在则不覆盖
    if instruments_file.exists():
        print(f"✅ 仪器数据已存在: {instruments_file}")
        return

    # 从 server.py 复制默认仪器数据
    instruments = [
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
    ]

    with open(instruments_file, "w", encoding="utf-8") as f:
        json.dump(instruments, f, ensure_ascii=False, indent=2)

    print(f"✅ 仪器数据已初始化: {instruments_file} ({len(instruments)} 台仪器)")


def init_empty_files():
    """初始化空记录文件"""
    files = {"records.json": [], "history.json": [], "pending.json": []}

    for filename, default_data in files.items():
        filepath = DATA_DIR / filename
        if not filepath.exists():
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            print(f"✅ {filename} 已创建")
        else:
            print(f"✅ {filename} 已存在")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 初始化仪器管理系统数据")
    print("=" * 60)

    init_users()
    init_instruments()
    init_empty_files()

    print("=" * 60)
    print("✅ 初始化完成！")
    print("=" * 60)
    print("\n启动服务器命令:")
    print("  python3 app.py")
    print("\n访问地址:")
    print("  http://127.0.0.1:8081/index_new.html")

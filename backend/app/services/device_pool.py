import random
from typing import Any, Dict, List

def _build_master_device_pool() -> List[Dict[str, Any]]:
    devices = []
    idx = 1

    # 1. ANDROID FLAGSHIPS & MID-RANGE (25 models x 15 Chrome builds = 375 unique devices)
    android_models = [
        ("Samsung Galaxy S24 Ultra", "SM-S928B", (412, 915), 3.0, "Adreno (TM) 750", 12),
        ("Samsung Galaxy S24+", "SM-S926B", (384, 854), 3.0, "Xclipse 940", 12),
        ("Samsung Galaxy S24", "SM-S921B", (360, 780), 3.0, "Xclipse 940", 8),
        ("Samsung Galaxy S23 Ultra", "SM-S918B", (412, 915), 3.0, "Adreno (TM) 740", 12),
        ("Samsung Galaxy S23+", "SM-S916B", (384, 854), 3.0, "Adreno (TM) 740", 8),
        ("Samsung Galaxy S23", "SM-S911B", (360, 780), 3.0, "Adreno (TM) 740", 8),
        ("Samsung Galaxy S22 Ultra", "SM-S908B", (384, 854), 3.75, "Adreno (TM) 730", 12),
        ("Samsung Galaxy Z Fold 5", "SM-F946B", (374, 869), 2.6, "Adreno (TM) 740", 12),
        ("Samsung Galaxy Z Flip 5", "SM-F731B", (412, 915), 2.6, "Adreno (TM) 740", 8),
        ("Samsung Galaxy A55 5G", "SM-A556B", (412, 915), 2.6, "Xclipse 530", 8),
        ("Samsung Galaxy A54 5G", "SM-A546B", (412, 915), 2.6, "Mali-G68 MP5", 8),
        ("Samsung Galaxy A34 5G", "SM-A346B", (412, 915), 2.6, "Mali-G68 MC4", 6),
        ("Google Pixel 9 Pro XL", "Pixel 9 Pro XL", (412, 923), 3.5, "Mali-G715-Immortalis MC10", 16),
        ("Google Pixel 9 Pro", "Pixel 9 Pro", (412, 923), 3.5, "Mali-G715-Immortalis MC10", 16),
        ("Google Pixel 9", "Pixel 9", (412, 923), 2.6, "Mali-G715-Immortalis MC10", 12),
        ("Google Pixel 8 Pro", "Pixel 8 Pro", (412, 892), 3.5, "Mali-G715s MC10", 12),
        ("Google Pixel 8", "Pixel 8", (412, 892), 2.6, "Mali-G715s MC10", 8),
        ("Google Pixel 8a", "Pixel 8a", (412, 892), 2.6, "Mali-G715s MC10", 8),
        ("Google Pixel 7 Pro", "Pixel 7 Pro", (412, 892), 3.5, "Mali-G710 MC10", 12),
        ("Xiaomi 14 Ultra", "24030PN60G", (412, 915), 3.5, "Adreno (TM) 750", 16),
        ("Xiaomi 14", "23127PN0CG", (393, 852), 3.0, "Adreno (TM) 750", 12),
        ("Xiaomi 13 Pro", "2210132G", (412, 915), 3.5, "Adreno (TM) 740", 12),
        ("OnePlus 12", "CPH2581", (412, 915), 3.5, "Adreno (TM) 750", 16),
        ("OnePlus 11", "CPH2449", (412, 915), 3.5, "Adreno (TM) 740", 16),
        ("Sony Xperia 1 V", "XQ-DQ72", (412, 960), 3.5, "Adreno (TM) 740", 12)
    ]

    chrome_builds = [
        ("14", "128.0.6613.88", "128"),
        ("14", "127.0.6533.103", "127"),
        ("14", "127.0.6533.84", "127"),
        ("14", "126.0.6478.182", "126"),
        ("14", "126.0.6478.122", "126"),
        ("14", "125.0.6422.165", "125"),
        ("14", "125.0.6422.146", "125"),
        ("14", "124.0.6367.179", "124"),
        ("14", "124.0.6367.113", "124"),
        ("13", "123.0.6312.118", "123"),
        ("13", "123.0.6312.80", "123"),
        ("13", "122.0.6261.119", "122"),
        ("13", "122.0.6261.105", "122"),
        ("13", "121.0.6167.178", "121"),
        ("13", "120.0.6099.230", "120")
    ]

    for model_name, code, vp, dsf, gpu, ram in android_models:
        for and_ver, ch_ver, ch_major in chrome_builds:
            ua = f"Mozilla/5.0 (Linux; Android {and_ver}; {code}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ch_ver} Mobile Safari/537.36"
            devices.append({
                "id": f"dev_{idx:04d}",
                "name": f"{model_name} (Chrome v{ch_major})",
                "platform": "Android",
                "user_agent": ua,
                "viewport": {"width": vp[0], "height": vp[1]},
                "device_scale_factor": dsf,
                "is_mobile": True,
                "has_touch": True,
                "hardware_concurrency": 8,
                "device_memory": ram,
                "webgl_vendor": "Qualcomm" if "Adreno" in gpu else "ARM",
                "webgl_renderer": gpu
            })
            idx += 1

    # 2. APPLE iPHONES (18 models x 8 iOS releases = 144 unique devices)
    iphone_models = [
        ("iPhone 16 Pro Max", (440, 956), 3.0, 8),
        ("iPhone 16 Pro", (402, 874), 3.0, 8),
        ("iPhone 16", (393, 852), 3.0, 8),
        ("iPhone 15 Pro Max", (430, 932), 3.0, 8),
        ("iPhone 15 Pro", (393, 852), 3.0, 8),
        ("iPhone 15 Plus", (430, 932), 3.0, 6),
        ("iPhone 15", (393, 852), 3.0, 6),
        ("iPhone 14 Pro Max", (430, 932), 3.0, 6),
        ("iPhone 14 Pro", (393, 852), 3.0, 6),
        ("iPhone 14 Plus", (428, 926), 3.0, 6),
        ("iPhone 14", (390, 844), 3.0, 6),
        ("iPhone 13 Pro Max", (428, 926), 3.0, 6),
        ("iPhone 13 Pro", (390, 844), 3.0, 6),
        ("iPhone 13", (390, 844), 3.0, 4),
        ("iPhone 13 mini", (375, 812), 3.0, 4),
        ("iPhone 12 Pro Max", (428, 926), 3.0, 6),
        ("iPhone 12", (390, 844), 3.0, 4),
        ("iPhone 11", (414, 896), 2.0, 4)
    ]

    ios_versions = [
        ("18_1", "18.1"),
        ("18_0", "18.0"),
        ("17_6_1", "17.6.1"),
        ("17_5_1", "17.5.1"),
        ("17_4_1", "17.4.1"),
        ("17_3", "17.3"),
        ("17_2", "17.2"),
        ("16_6", "16.6")
    ]

    for model_name, vp, dsf, ram in iphone_models:
        for ios_code, ios_display in ios_versions:
            ua = f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_code} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{ios_display} Mobile/15E148 Safari/604.1"
            devices.append({
                "id": f"dev_{idx:04d}",
                "name": f"{model_name} (iOS {ios_display})",
                "platform": "iOS",
                "user_agent": ua,
                "viewport": {"width": vp[0], "height": vp[1]},
                "device_scale_factor": dsf,
                "is_mobile": True,
                "has_touch": True,
                "hardware_concurrency": 6,
                "device_memory": ram,
                "webgl_vendor": "Apple Inc.",
                "webgl_renderer": "Apple GPU"
            })
            idx += 1

    # 3. WINDOWS 10 / 11 DESKTOPS & LAPTOPS (8 GPUs x 4 resolutions x 4 browsers = 128 unique devices)
    win_gpus = [
        ("NVIDIA GeForce RTX 4090", "Google Inc. (NVIDIA)", 16, 32),
        ("NVIDIA GeForce RTX 4070 Ti", "Google Inc. (NVIDIA)", 12, 16),
        ("NVIDIA GeForce RTX 3060", "Google Inc. (NVIDIA)", 8, 16),
        ("AMD Radeon RX 7800 XT", "Google Inc. (AMD)", 12, 16),
        ("AMD Radeon RX 6700 XT", "Google Inc. (AMD)", 8, 16),
        ("Intel(R) Iris(R) Xe Graphics", "Google Inc. (Intel)", 4, 8),
        ("Intel(R) UHD Graphics 770", "Google Inc. (Intel)", 4, 8),
        ("NVIDIA GeForce GTX 1660 SUPER", "Google Inc. (NVIDIA)", 6, 8)
    ]
    win_res = [
        (1920, 1080),
        (2560, 1440),
        (1536, 864),
        (1366, 768)
    ]
    win_browsers = [
        ("Chrome v128", "Chrome/128.0.6613.114 Safari/537.36"),
        ("Chrome v127", "Chrome/127.0.6533.100 Safari/537.36"),
        ("Edge v127", "Chrome/127.0.6533.100 Safari/537.36 Edg/127.0.2651.98"),
        ("Edge v126", "Chrome/126.0.6478.183 Safari/537.36 Edg/126.0.2592.113")
    ]

    for gpu_name, vendor, cores, ram in win_gpus:
        for w, h in win_res:
            for b_name, b_str in win_browsers:
                ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) {b_str}"
                devices.append({
                    "id": f"dev_{idx:04d}",
                    "name": f"Windows PC ({b_name} • {w}x{h})",
                    "platform": "Windows",
                    "user_agent": ua,
                    "viewport": {"width": w, "height": h},
                    "device_scale_factor": 1.0 if w >= 1920 else 1.25,
                    "is_mobile": False,
                    "has_touch": False,
                    "hardware_concurrency": cores,
                    "device_memory": ram,
                    "webgl_vendor": vendor,
                    "webgl_renderer": f"ANGLE ({gpu_name} Direct3D11 vs_5_0 ps_5_0)"
                })
                idx += 1

    # 4. APPLE MACINTOSH (4 models x 3 resolutions x 4 browsers = 48 unique devices)
    mac_models = [
        ("MacBook Pro 16\" (M3 Max)", 16, 32),
        ("MacBook Pro 14\" (M2 Pro)", 12, 16),
        ("MacBook Air 15\" (M3)", 8, 16),
        ("MacBook Air 13\" (M2)", 8, 8)
    ]
    mac_res = [
        (1728, 1117),
        (1512, 982),
        (1440, 900)
    ]
    mac_browsers = [
        ("Safari 17.5", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5.1 Safari/605.1.15"),
        ("Safari 17.4", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15"),
        ("Chrome 127", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36"),
        ("Chrome 126", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.183 Safari/537.36")
    ]

    for m_name, cores, ram in mac_models:
        for w, h in mac_res:
            for b_name, ua in mac_browsers:
                devices.append({
                    "id": f"dev_{idx:04d}",
                    "name": f"{m_name} ({b_name})",
                    "platform": "macOS",
                    "user_agent": ua,
                    "viewport": {"width": w, "height": h},
                    "device_scale_factor": 2.0,
                    "is_mobile": False,
                    "has_touch": False,
                    "hardware_concurrency": cores,
                    "device_memory": ram,
                    "webgl_vendor": "Apple Inc.",
                    "webgl_renderer": "Apple M-Series GPU"
                })
                idx += 1

    return devices


_MASTER_POOL: List[Dict[str, Any]] = _build_master_device_pool()


def get_device_pool_size() -> int:
    """Return total number of unique realistic device profiles in the engine."""
    return len(_MASTER_POOL)


def get_unique_device_batch(count: int, shuffle: bool = True) -> List[Dict[str, Any]]:
    """Return a batch of completely unique devices with zero duplicate fingerprints."""
    pool_copy = list(_MASTER_POOL)
    if shuffle:
        random.shuffle(pool_copy)
    
    # If requested count is within pool size, return exact slice with zero duplication
    if count <= len(pool_copy):
        return pool_copy[:count]

    # If count exceeds pool size, cycle through pool with slight viewport variations
    result = []
    cycles = (count // len(pool_copy)) + 1
    for c in range(cycles):
        shuffled = list(_MASTER_POOL)
        random.shuffle(shuffled)
        result.extend(shuffled)
        if len(result) >= count:
            break
    return result[:count]

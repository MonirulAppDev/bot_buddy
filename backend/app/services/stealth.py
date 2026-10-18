import random
from typing import Any, Dict


def generate_wifi_profile(view_idx: int) -> Dict[str, str]:
    """Generates unique WiFi network parameters (LAN IPv4, BSSID/MAC, SSID, gateway) for every view."""
    # Common router vendors: TP-Link, Netgear, ASUS, Linksys, D-Link, Huawei, Spectrum, Comcast
    bssid_prefixes = [
        "c0:4a:00", "00:1a:2b", "f4:d4:88", "b8:27:eb", "30:b5:c2",
        "84:16:f9", "ec:08:6b", "a4:2b:b0", "dc:ef:09", "50:d4:f7"
    ]
    ssid_templates = [
        "Home_WiFi_5G_{suffix}",
        "TP-Link_5G_{suffix}",
        "NETGEAR_88_{suffix}",
        "SpectrumSetup-{suffix}",
        "Xfinity_Mobile_{suffix}",
        "ASUS_Gaming_{suffix}",
        "ATT_Fiber_{suffix}",
        "Fiber_Ultra_{suffix}",
        "Office_Guest_{suffix}",
        "My_Galaxy_Hotspot_{suffix}"
    ]

    prefix = random.choice(bssid_prefixes)
    b_tail = f"{random.randint(10, 99):02x}:{random.randint(10, 99):02x}:{random.randint(10, 99):02x}"
    mac_address = f"{prefix}:{b_tail}"

    subnet = random.choice(["192.168.1", "192.168.0", "10.0.0", "172.16.1"])
    host_num = random.randint(12, 245)
    local_ipv4 = f"{subnet}.{host_num}"
    gateway_ipv4 = f"{subnet}.1"

    suffix = f"{random.randint(1000, 9999):04d}"
    ssid = random.choice(ssid_templates).format(suffix=suffix)

    return {
        "mac_address": mac_address,
        "local_ipv4": local_ipv4,
        "gateway_ipv4": gateway_ipv4,
        "ssid": ssid,
        "dns": random.choice(["1.1.1.1", "8.8.8.8", "8.8.4.4", "9.9.9.9"]),
        "signal_strength": f"-{random.randint(38, 65)} dBm"
    }


def build_stealth_injection_script(device: Dict[str, Any], wifi: Dict[str, str], view_idx: int) -> str:
    """Builds a dynamic, per-session anti-bot script that spoofs hardware, GPU, WebRTC, Canvas, Audio, Battery & WiFi."""
    vendor = device.get("webgl_vendor", "Qualcomm")
    renderer = device.get("webgl_renderer", "Adreno (TM) 750")
    cores = device.get("hardware_concurrency", 8)
    ram = device.get("device_memory", 8)
    is_mobile = device.get("is_mobile", True)
    platform = device.get("platform", "Android")
    downlink = round(random.uniform(9.0, 48.0), 1)
    rtt = random.randint(25, 80)
    battery_level = round(random.uniform(0.40, 0.96), 2)
    is_charging = random.choice([True, False])
    local_ip = wifi["local_ipv4"]

    script = f"""
    (() => {{
        // 1. Anti-Automation & Webdriver Elimination
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
        delete navigator.__proto__.webdriver;

        // 2. Hardware Concurrency & Memory Spoofing
        Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {cores} }});
        Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {ram} }});
        Object.defineProperty(navigator, 'maxTouchPoints', {{ get: () => {5 if is_mobile else 0} }});

        // 3. Network Information API (Simulating Real WiFi / 4G Interface)
        const connectionInfo = {{
            effectiveType: '4g',
            rtt: {rtt},
            downlink: {downlink},
            saveData: false,
            type: 'wifi',
            onchange: null
        }};
        try {{
            Object.defineProperty(navigator, 'connection', {{ get: () => connectionInfo }});
            Object.defineProperty(navigator, 'mozConnection', {{ get: () => connectionInfo }});
            Object.defineProperty(navigator, 'webkitConnection', {{ get: () => connectionInfo }});
        }} catch(e) {{}}

        // 4. WebRTC IP Leak Shield (Virtual WiFi LAN IP: {local_ip})
        // Intercept RTCPeerConnection to replace any host candidates with our unique virtual WiFi IP
        if (window.RTCPeerConnection) {{
            const OrigPeer = window.RTCPeerConnection;
            window.RTCPeerConnection = function(...args) {{
                const pc = new OrigPeer(...args);
                const origSetLocal = pc.setLocalDescription.bind(pc);
                pc.setLocalDescription = async function(desc) {{
                    if (desc && desc.sdp) {{
                        // Rewrite IP addresses inside SDP to unique simulated WiFi IP
                        desc.sdp = desc.sdp.replace(
                            /(\\b(?:192\\.168|10\\.|172\\.(?:1[6-9]|2[0-9]|3[0-1]))\\.[0-9]+\\.[0-9]+\\b)/g,
                            '{local_ip}'
                        );
                    }}
                    return origSetLocal(desc);
                }};
                return pc;
            }};
            window.RTCPeerConnection.prototype = OrigPeer.prototype;
        }}

        // 5. Deep WebGL Vendor & Renderer Hardware Spoofing
        const getParameterMock = (target) => {{
            const origGetParam = target.prototype.getParameter;
            target.prototype.getParameter = function(param) {{
                // UNMASKED_VENDOR_WEBGL
                if (param === 37445) return '{vendor}';
                // UNMASKED_RENDERER_WEBGL
                if (param === 37446) return '{renderer}';
                return origGetParam.apply(this, arguments);
            }};
        }};
        if (window.WebGLRenderingContext) getParameterMock(WebGLRenderingContext);
        if (window.WebGL2RenderingContext) getParameterMock(WebGL2RenderingContext);

        // 6. Canvas Fingerprint Entropy (Deterministic Micro-Noise for View #{view_idx})
        const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type, ...args) {{
            const ctx = this.getContext('2d');
            if (ctx && this.width > 0 && this.height > 0) {{
                try {{
                    const imgData = ctx.getImageData(0, 0, Math.min(this.width, 16), Math.min(this.height, 16));
                    // Shift pixel data by view_idx mod 2 for unique canvas hash without visual change
                    imgData.data[0] = (imgData.data[0] ^ ({view_idx} % 3)) & 0xFF;
                    ctx.putImageData(imgData, 0, 0);
                }} catch(e) {{}}
            }}
            return origToDataURL.apply(this, [type, ...args]);
        }};

        // 7. AudioContext Fingerprint Randomization
        if (window.AudioBuffer) {{
            const origGetChannelData = AudioBuffer.prototype.getChannelData;
            AudioBuffer.prototype.getChannelData = function(channel) {{
                const data = origGetChannelData.apply(this, arguments);
                if (data && data.length > 0) {{
                    data[0] += ({view_idx} * 0.00000001);
                }}
                return data;
            }};
        }}

        // 8. Battery API Emulation
        if (navigator.getBattery) {{
            navigator.getBattery = () => Promise.resolve({{
                charging: {str(is_charging).lower()},
                chargingTime: {0 if is_charging else random.randint(1200, 3600)},
                dischargingTime: {random.randint(7200, 24000) if not is_charging else 99999},
                level: {battery_level},
                addEventListener: () => {{}},
                removeEventListener: () => {{}}
            }});
        }}

        // 9. Chrome Runtime / Safari Platform Matching
        {"window.chrome = { app: { isInstalled: false }, runtime: { PlatformOs: { ANDROID: 'android' } } };" if "Android" in platform or "Windows" in platform else "delete window.chrome;"}

        // 10. Notifications Permission Query Override
        if (navigator.permissions && navigator.permissions.query) {{
            const origQuery = navigator.permissions.query;
            navigator.permissions.query = (param) => (
                param.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    origQuery(param)
            );
        }}
    }})();
    """
    return script

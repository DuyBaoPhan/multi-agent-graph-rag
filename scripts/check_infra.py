import socket
from loguru import logger

def check_port(host, port, service_name):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        try:
            s.connect((host, port))
            logger.info(f"✅ {service_name} is UP on {host}:{port}")
            return True
        except:
            logger.error(f"❌ {service_name} is DOWN on {host}:{port}")
            return False

if __name__ == "__main__":
    print("\n--- INFRASTRUCTURE DIAGNOSTIC ---")
    n = check_port("localhost", 7687, "Neo4j (Bolt)")
    r = check_port("localhost", 6379, "Redis")
    
    if n and r:
        print("\n🎉 Mọi thứ đã sẵn sàng! Bạn có thể chạy 'uvicorn' ngay.")
    else:
        print("\n⚠️ Vẫn còn lỗi kết nối. Hãy đảm bảo Docker Desktop đang chạy.")

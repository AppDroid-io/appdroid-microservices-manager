# app/services/mdns.py
import socket
from zeroconf import ServiceInfo, Zeroconf

class mDNSRegistrar:
    """
    (EN) Manages the registration and unregistration of the service via mDNS (Zeroconf).
    (ES) Gestiona el registro y la anulación del registro del servicio a través de mDNS (Zeroconf).
    """
    def __init__(self, port: int = 8000):
        self.zeroconf = Zeroconf()
        self.port = port
        self.info = None

    def register(self):
        """
        (EN) Gathers host info and registers the service on the local network.
        (ES) Recopila información del host y registra el servicio en la red local.
        """
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            
            self.info = ServiceInfo(
                type_="_appdroid-manager._tcp.local.",
                name=f"AppDroid Manager Python._appdroid-manager._tcp.local.",
                addresses=[socket.inet_aton(ip_address)],
                port=self.port,
                properties={'version': '0.2.0', 'stack': 'FastAPI'},
            )
            
            print("INFO:     Registering service with mDNS...")
            self.zeroconf.register_service(self.info)
            print(f"INFO:     mDNS service registered as 'AppDroid Manager Python' at {ip_address}:{self.port}")

        except Exception as e:
            print(f"ERROR:    Could not register mDNS service: {e}")

    def unregister(self):
        """
        (EN) Unregisters the service from the local network.
        (ES) Anula el registro del servicio de la red local.
        """
        if self.info:
            print("INFO:     Unregistering mDNS service...")
            self.zeroconf.unregister_service(self.info)
            self.zeroconf.close()
            print("INFO:     mDNS service unregistered.")
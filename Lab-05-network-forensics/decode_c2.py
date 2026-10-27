#!/usr/bin/env python3
"""
decode_c2.py — décode le canal caché de la porte dérobée (Lab 05).

La porte dérobée (backdoor.py) reçoit chaque commande en hexadécimal, puis la
passe dans xor(message, KEY) avec KEY = "super_secret_key". On réutilise ici
exactement la même routine pour désobfusquer les commandes capturées sur le
port 5555.

Utilisation :
    python3 decode_c2.py
"""


def xor(message, key="super_secret_key"):
    message = bytes.fromhex(message)          # la commande arrive en hexadécimal
    key = key.encode()
    xor_key = (key * (len(message) // len(key) + 1))[:len(message)]  # clé répétée
    return bytes([a ^ b for a, b in zip(message, xor_key)]).decode()


# Chaînes relevées dans le flux tcp.port == 5555
hex_captures = [
    "1f067a",
    "1a117a",
    "10140445152d4355175c110c2b61",
    "1616180a527d150902151e176f05020b1201033a43392c1c53073a196b0f"
    "562642012f1143331f3a0b41174700080d4d1e050d47522353120b1d04193661",
]

if __name__ == "__main__":
    for h in hex_captures:
        print(f"{h[:16]:<18}->  {xor(h)!r}")

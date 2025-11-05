from __future__ import annotations
import binascii
import hashlib
from typing import List, Optional

from ecdsa import SECP256k1, SigningKey
from Crypto.Hash import RIPEMD160
import base58
from eth_keys import keys as eth_keys
from eth_utils import to_checksum_address


class AddressUtils:
    @staticmethod
    def derive_addresses_from_artifact(artifact: Optional[str], chain_hint: Optional[str] = None) -> List[dict]:
        if not artifact:
            return []
        artifact = artifact.strip()

        out: List[dict] = []

        # ETH private key (with or without 0x)
        pk = AddressUtils._parse_eth_privkey(artifact)
        if pk:
            try:
                addr = AddressUtils.eth_address_from_privkey(pk)
                out.append({'chain': 'eth', 'address': addr})
            except Exception:  # noqa: BLE001
                pass

        # BTC WIF
        if AddressUtils._looks_like_wif(artifact):
            try:
                priv, compressed, _ = AddressUtils.wif_to_privkey_bytes(artifact)
                addr = AddressUtils.btc_p2pkh_from_privkey(priv, compressed=compressed)
                out.append({'chain': 'btc', 'address': addr})
            except Exception:  # noqa: BLE001
                pass

        return out

    @staticmethod
    def _parse_eth_privkey(s: str) -> Optional[str]:
        hex_s = None
        if s.startswith('0x') and len(s) == 66:
            hex_s = s[2:]
        elif len(s) == 64 and all(c in '0123456789abcdefABCDEF' for c in s):
            hex_s = s
        if hex_s and len(hex_s) == 64:
            return hex_s.lower()
        return None

    @staticmethod
    def _looks_like_wif(s: str) -> bool:
        if len(s) not in (51, 52):
            return False
        return s[0] in ('5', 'K', 'L') and all(c in '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz' for c in s)

    @staticmethod
    def eth_address_from_privkey(privkey_hex: str) -> str:
        pk_bytes = binascii.unhexlify(privkey_hex)
        pk = eth_keys.PrivateKey(pk_bytes)
        addr = pk.public_key.to_checksum_address()
        return addr

    @staticmethod
    def wif_to_privkey_bytes(wif: str):
        # WIF = base58check(0x80 + privkey + optional 0x01 if compressed)
        decoded = base58.b58decode_check(wif)
        if decoded[0] != 0x80:
            raise ValueError('Not a mainnet WIF')
        if len(decoded) == 34 and decoded[-1] == 0x01:
            # 0x80 + 32 + 0x01
            return decoded[1:-1], True, 'mainnet'
        elif len(decoded) == 33:
            return decoded[1:], False, 'mainnet'
        else:
            raise ValueError('Invalid WIF length')

    @staticmethod
    def btc_p2pkh_from_privkey(privkey: bytes, compressed: bool = True) -> str:
        sk = SigningKey.from_string(privkey, curve=SECP256k1)
        vk = sk.get_verifying_key()
        if compressed:
            px = vk.pubkey.point.x()
            py = vk.pubkey.point.y()
            parity = 0x02 | (py & 1)
            pub = bytes([parity]) + px.to_bytes(32, 'big')
        else:
            pub = b'\x04' + vk.to_string()

        sha = hashlib.sha256(pub).digest()
        ripe = RIPEMD160.new(sha).digest()
        versioned = b'\x00' + ripe  # mainnet P2PKH
        checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
        return base58.b58encode(versioned + checksum).decode()

    @staticmethod
    def explorer_links(addr: str) -> List[str]:
        # Guess chain by prefix
        links: List[str] = []
        if addr.startswith('0x') and len(addr) == 42:
            # ETH
            links.append(f'https://etherscan.io/address/{addr}')
        elif addr.startswith('1') or addr.startswith('3') or addr.startswith('bc1'):
            links.append(f'https://www.blockchain.com/btc/address/{addr}')
            links.append(f'https://blockstream.info/address/{addr}')
        else:
            # unknown chain
            pass
        return links

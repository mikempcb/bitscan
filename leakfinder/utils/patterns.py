import re
from typing import List, Pattern


class LeakPatterns:
    # Core regex patterns for leaked material
    ETH_PRIVKEY = re.compile(r"\b0x[a-fA-F0-9]{64}\b")
    ETH_PRIVKEY_HEX = re.compile(r"\b[a-fA-F0-9]{64}\b")
    BTC_WIF = re.compile(r"\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b")
    XPRV = re.compile(r"\bxprv[1-9A-HJ-NP-Za-km-z]{78,}\b")
    KEYSTORE_HINT = re.compile(r"\b(keystore|UTC--\d{4}-\d{2}-\d{2}T)\b", re.IGNORECASE)
    MNEMONIC_HINT = re.compile(r"\b(mnemonic|seed phrase|bip39)\b", re.IGNORECASE)

    @classmethod
    def build(cls, kinds: List[str]) -> List[Pattern]:
        patterns: List[Pattern] = []
        if not kinds:
            kinds = ['eth_priv', 'btc_wif', 'xprv', 'keystore', 'mnemonic']
        if 'eth_priv' in kinds:
            patterns.append(cls.ETH_PRIVKEY)
            patterns.append(cls.ETH_PRIVKEY_HEX)
        if 'btc_wif' in kinds:
            patterns.append(cls.BTC_WIF)
        if 'xprv' in kinds:
            patterns.append(cls.XPRV)
        if 'keystore' in kinds:
            patterns.append(cls.KEYSTORE_HINT)
        if 'mnemonic' in kinds:
            patterns.append(cls.MNEMONIC_HINT)
        return patterns


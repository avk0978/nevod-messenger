"""
Cryptographic primitives for Nevod.

Signing:    Ed25519  (identity, authentication)
Encryption: X25519 + ChaCha20-Poly1305  (E2E, ephemeral key per message)
KDF:        SHA-256 of the raw X25519 shared secret (matches iOS/PWA clients — see _kdf)
ZKP:        Schnorr on Edwards25519 (interactive, Fiat-Shamir transcript)
"""

import hashlib
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


RAW = serialization.Encoding.Raw
RAW_PUB = serialization.PublicFormat.Raw
RAW_PRIV = serialization.PrivateFormat.Raw
NO_ENC = serialization.NoEncryption()

NONCE_SIZE = 12


@dataclass
class SigningKeypair:
    private: Ed25519PrivateKey
    public: bytes   # 32 raw bytes = node_id / cell_id


@dataclass
class EncryptionKeypair:
    private: X25519PrivateKey
    public: bytes   # 32 raw bytes = published enc pubkey


def gen_signing() -> SigningKeypair:
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key().public_bytes(RAW, RAW_PUB)
    return SigningKeypair(private=priv, public=pub)


def gen_encryption() -> EncryptionKeypair:
    priv = X25519PrivateKey.generate()
    pub = priv.public_key().public_bytes(RAW, RAW_PUB)
    return EncryptionKeypair(private=priv, public=pub)


def sign(message: bytes, signing_key: SigningKeypair) -> bytes:
    return signing_key.private.sign(message)


def verify(message: bytes, signature: bytes, pubkey_bytes: bytes) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(pubkey_bytes).verify(signature, message)
        return True
    except InvalidSignature:
        return False


def encrypt(plaintext: bytes, recipient_enc_pubkey: bytes) -> dict:
    """
    Encrypt plaintext for recipient.
    Returns dict with ephemeral_pubkey, nonce, ciphertext.
    recipient_enc_pubkey: X25519 public key (32 bytes).
    """
    ephemeral = X25519PrivateKey.generate()
    recipient = X25519PublicKey.from_public_bytes(recipient_enc_pubkey)
    shared = ephemeral.exchange(recipient)
    key = _kdf(shared, ephemeral.public_key().public_bytes(RAW, RAW_PUB))

    nonce = os.urandom(NONCE_SIZE)
    ciphertext = ChaCha20Poly1305(key).encrypt(nonce, plaintext, None)

    return {
        "ephemeral_pubkey": ephemeral.public_key().public_bytes(RAW, RAW_PUB),
        "nonce": nonce,
        "ciphertext": ciphertext,
    }


def decrypt(ciphertext: bytes, nonce: bytes, ephemeral_pubkey: bytes,
            enc_keypair: EncryptionKeypair) -> bytes:
    """
    Decrypt E2E message.
    Raises cryptography.exceptions.InvalidTag on auth failure.
    """
    ephemeral_pub = X25519PublicKey.from_public_bytes(ephemeral_pubkey)
    shared = enc_keypair.private.exchange(ephemeral_pub)
    key = _kdf(shared, ephemeral_pubkey)
    return ChaCha20Poly1305(key).decrypt(nonce, ciphertext, None)


def _kdf(shared_secret: bytes, ephemeral_pubkey: bytes) -> bytes:
    # Matches both real clients exactly (iOS CryptoManager.swift, PWA nevod.js):
    # plain SHA-256 of the raw X25519 shared secret, no salt/info. This used to
    # be a proper HKDF here, which quietly never interoperated with either
    # client — nothing previously exercised Python encrypt/decrypt against a
    # real iOS/PWA message, so the mismatch went unnoticed. ephemeral_pubkey
    # kept as a parameter for call-site compatibility even though it's unused.
    return hashlib.sha256(shared_secret).digest()


def signing_priv_to_bytes(key: Ed25519PrivateKey) -> bytes:
    return key.private_bytes(RAW, RAW_PRIV, NO_ENC)


def signing_priv_from_bytes(b: bytes) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(b)


def enc_priv_to_bytes(key: X25519PrivateKey) -> bytes:
    return key.private_bytes(RAW, RAW_PRIV, NO_ENC)


def enc_priv_from_bytes(b: bytes) -> X25519PrivateKey:
    return X25519PrivateKey.from_private_bytes(b)


# ─── Schnorr ZKP on Edwards25519 ─────────────────────────────────────────────
# Pure-Python extended-coordinate arithmetic avoids modular inversion in the
# inner loop (only one inversion per scalar mult, at the final affine convert).

_P = 2**255 - 19
L  = 2**252 + 27742317777372353535851937790883648493  # group order

_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_I = pow(2, (_P - 1) // 4, _P)  # sqrt(-1) mod P

# Base point G — extended coords (X:Y:Z:T) with x=X/Z, y=Y/Z, T=x·y
_Gy   = 4 * pow(5, _P - 2, _P) % _P
_Gy2  = _Gy * _Gy % _P
_Gx2  = (_Gy2 - 1) * pow(_D * _Gy2 + 1, _P - 2, _P) % _P
_Gx   = pow(_Gx2, (_P + 3) // 8, _P)
if (_Gx * _Gx - _Gx2) % _P != 0:
    _Gx = _Gx * _I % _P
# Standard Ed25519 base point G encodes as 5866...66, meaning sign(x) = 0 (x is even).
# Select the even square root.
if _Gx & 1:
    _Gx = (_P - _Gx) % _P
_G_ext = (_Gx, _Gy, 1, _Gx * _Gy % _P)


def _ext_add(P1: tuple, P2: tuple) -> tuple:
    """Unified addition on twisted Edwards25519 (a=-1) in extended coordinates."""
    X1, Y1, Z1, T1 = P1
    X2, Y2, Z2, T2 = P2
    A = (Y1 - X1) * (Y2 - X2) % _P
    B = (Y1 + X1) * (Y2 + X2) % _P
    C = 2 * _D * T1 * T2 % _P
    D = 2 * Z1 * Z2 % _P
    E = (B - A) % _P
    F = (D - C) % _P
    G = (D + C) % _P
    H = (B + A) % _P
    return E * F % _P, G * H % _P, F * G % _P, E * H % _P


def _ext_scale(k: int, P: tuple) -> tuple:
    """Scalar multiplication via double-and-add in extended coordinates."""
    Q = (0, 1, 1, 0)  # identity element
    k = k % L
    while k:
        if k & 1:
            Q = _ext_add(Q, P)
        P = _ext_add(P, P)
        k >>= 1
    return Q


def _to_affine(P: tuple) -> tuple:
    X, Y, Z, _ = P
    zi = pow(Z, _P - 2, _P)
    return X * zi % _P, Y * zi % _P


def _enc_point(x: int, y: int) -> bytes:
    b = bytearray(y.to_bytes(32, 'little'))
    if x & 1:
        b[31] |= 0x80
    return bytes(b)


def _dec_point(b: bytes) -> tuple:
    b = bytearray(b)
    sign = b[31] >> 7
    b[31] &= 0x7F
    y = int.from_bytes(b, 'little')
    if y >= _P:
        raise ValueError("Ed25519 point y out of range")
    y2 = y * y % _P
    x2 = (y2 - 1) * pow(_D * y2 + 1, _P - 2, _P) % _P
    if x2 == 0:
        return 0, y
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P != 0:
        x = x * _I % _P
    if (x * x - x2) % _P != 0:
        raise ValueError("Ed25519 point: no square root")
    if (x & 1) != sign:
        x = (_P - x) % _P
    return x, y


def _privkey_scalar(privkey: Ed25519PrivateKey) -> int:
    """Extract clamped scalar from Ed25519 private key (SHA-512 + bit clamp)."""
    seed = privkey.private_bytes(RAW, RAW_PRIV, NO_ENC)
    h = bytearray(hashlib.sha512(seed).digest()[:32])
    h[0] &= 248   # clear bits 0,1,2
    h[31] &= 127  # clear bit 255
    h[31] |= 64   # set bit 254
    return int.from_bytes(h, 'little')


def schnorr_commit(privkey: Ed25519PrivateKey) -> tuple:
    """
    Generate Schnorr commitment R = r·G.
    Returns (r_bytes, R_bytes). r is ephemeral — use once, keep secret.
    """
    r_int = int.from_bytes(os.urandom(32), 'little') % L
    if r_int == 0:
        r_int = 1
    R_bytes = _enc_point(*_to_affine(_ext_scale(r_int, _G_ext)))
    return r_int.to_bytes(32, 'little'), R_bytes


def schnorr_prove(privkey: Ed25519PrivateKey, r_bytes: bytes, c_int: int) -> bytes:
    """Compute Schnorr response s = (r + c·x) mod L."""
    r_int = int.from_bytes(r_bytes, 'little')
    x_int = _privkey_scalar(privkey)
    return ((r_int + c_int * x_int) % L).to_bytes(32, 'little')


def schnorr_verify(pubkey_bytes: bytes, R_bytes: bytes, c_int: int, s_bytes: bytes) -> bool:
    """
    Verify Schnorr proof: s·G == R + c·X
    pubkey_bytes: 32-byte Ed25519 public key (= point X = x·G)
    """
    try:
        s_int = int.from_bytes(s_bytes, 'little') % L
        Rx, Ry = _dec_point(R_bytes)
        Xx, Xy = _dec_point(pubkey_bytes)
        R_ext = (Rx, Ry, 1, Rx * Ry % _P)
        X_ext = (Xx, Xy, 1, Xx * Xy % _P)
        sG   = _to_affine(_ext_scale(s_int, _G_ext))
        cX   = _to_affine(_ext_scale(c_int % L, X_ext))
        cX_ext = (cX[0], cX[1], 1, cX[0] * cX[1] % _P)
        RcX  = _to_affine(_ext_add(R_ext, cX_ext))
        return sG == RcX
    except Exception:
        return False

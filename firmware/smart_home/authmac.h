// authmac.h - portable SHA-256 and HMAC-SHA256 for authenticated commands.
//
// Self-contained so the same code runs on the ESP32 and in the host test harness,
// and so the authentication logic can be unit-tested against known answers on a PC.
// SHA-256 is the FIPS 180-4 reference algorithm; the HMAC construction is RFC 2104.
//
// This is used only to VERIFY a short authentication tag on an incoming command and
// to size a replay counter. It is not a general crypto library.
#pragma once
#include <stdint.h>
#include <string.h>

namespace authmac {

struct Sha256 {
  uint32_t s[8];
  uint64_t len;
  uint8_t  buf[64];
  uint32_t n;
};

static inline uint32_t rotr(uint32_t x, int r) { return (x >> r) | (x << (32 - r)); }

static inline void sha256_block(Sha256& c, const uint8_t* p) {
  static const uint32_t K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
  uint32_t w[64];
  for (int i = 0; i < 16; i++)
    w[i] = (uint32_t)p[i*4] << 24 | (uint32_t)p[i*4+1] << 16 | (uint32_t)p[i*4+2] << 8 | p[i*4+3];
  for (int i = 16; i < 64; i++) {
    uint32_t s0 = rotr(w[i-15],7) ^ rotr(w[i-15],18) ^ (w[i-15] >> 3);
    uint32_t s1 = rotr(w[i-2],17) ^ rotr(w[i-2],19) ^ (w[i-2] >> 10);
    w[i] = w[i-16] + s0 + w[i-7] + s1;
  }
  uint32_t a=c.s[0],b=c.s[1],cc=c.s[2],d=c.s[3],e=c.s[4],f=c.s[5],g=c.s[6],h=c.s[7];
  for (int i = 0; i < 64; i++) {
    uint32_t S1 = rotr(e,6) ^ rotr(e,11) ^ rotr(e,25);
    uint32_t ch = (e & f) ^ (~e & g);
    uint32_t t1 = h + S1 + ch + K[i] + w[i];
    uint32_t S0 = rotr(a,2) ^ rotr(a,13) ^ rotr(a,22);
    uint32_t maj = (a & b) ^ (a & cc) ^ (b & cc);
    uint32_t t2 = S0 + maj;
    h=g; g=f; f=e; e=d+t1; d=cc; cc=b; b=a; a=t1+t2;
  }
  c.s[0]+=a; c.s[1]+=b; c.s[2]+=cc; c.s[3]+=d; c.s[4]+=e; c.s[5]+=f; c.s[6]+=g; c.s[7]+=h;
}

static inline void sha256_init(Sha256& c) {
  c.s[0]=0x6a09e667; c.s[1]=0xbb67ae85; c.s[2]=0x3c6ef372; c.s[3]=0xa54ff53a;
  c.s[4]=0x510e527f; c.s[5]=0x9b05688c; c.s[6]=0x1f83d9ab; c.s[7]=0x5be0cd19;
  c.len = 0; c.n = 0;
}

static inline void sha256_update(Sha256& c, const uint8_t* p, size_t n) {
  c.len += n;
  while (n) {
    size_t take = 64 - c.n; if (take > n) take = n;
    memcpy(c.buf + c.n, p, take);
    c.n += (uint32_t)take; p += take; n -= take;
    if (c.n == 64) { sha256_block(c, c.buf); c.n = 0; }
  }
}

static inline void sha256_final(Sha256& c, uint8_t out[32]) {
  uint64_t bits = c.len * 8;
  uint8_t pad = 0x80;
  sha256_update(c, &pad, 1);
  uint8_t zero = 0;
  while (c.n != 56) sha256_update(c, &zero, 1);
  uint8_t lenbuf[8];
  for (int i = 0; i < 8; i++) lenbuf[i] = (uint8_t)(bits >> (56 - i*8));
  sha256_update(c, lenbuf, 8);
  for (int i = 0; i < 8; i++) {
    out[i*4]   = (uint8_t)(c.s[i] >> 24);
    out[i*4+1] = (uint8_t)(c.s[i] >> 16);
    out[i*4+2] = (uint8_t)(c.s[i] >> 8);
    out[i*4+3] = (uint8_t)(c.s[i]);
  }
}

// HMAC-SHA256(key, msg) -> out[32]  (RFC 2104)
static inline void hmac_sha256(const uint8_t* key, size_t keyLen,
                               const uint8_t* msg, size_t msgLen, uint8_t out[32]) {
  uint8_t k[64];
  memset(k, 0, sizeof k);
  if (keyLen > 64) {
    Sha256 c; sha256_init(c); sha256_update(c, key, keyLen); sha256_final(c, k);
  } else {
    memcpy(k, key, keyLen);
  }
  uint8_t ipad[64], opad[64];
  for (int i = 0; i < 64; i++) { ipad[i] = k[i] ^ 0x36; opad[i] = k[i] ^ 0x5c; }
  uint8_t inner[32];
  { Sha256 c; sha256_init(c); sha256_update(c, ipad, 64); sha256_update(c, msg, msgLen); sha256_final(c, inner); }
  { Sha256 c; sha256_init(c); sha256_update(c, opad, 64); sha256_update(c, inner, 32); sha256_final(c, out); }
}

// Constant-time comparison, so a wrong tag does not leak how many bytes matched.
static inline bool ct_equal(const uint8_t* a, const uint8_t* b, size_t n) {
  uint8_t diff = 0;
  for (size_t i = 0; i < n; i++) diff |= (uint8_t)(a[i] ^ b[i]);
  return diff == 0;
}

static inline int hex_nibble(char ch) {
  if (ch >= '0' && ch <= '9') return ch - '0';
  if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
  if (ch >= 'A' && ch <= 'F') return ch - 'A' + 10;
  return -1;
}

// Parse up to maxOut bytes of hex. Returns number of bytes, or -1 on a bad character.
static inline int hex_decode(const char* s, size_t slen, uint8_t* out, size_t maxOut) {
  if (slen % 2) return -1;
  size_t bytes = slen / 2;
  if (bytes > maxOut) return -1;
  for (size_t i = 0; i < bytes; i++) {
    int hi = hex_nibble(s[i*2]), lo = hex_nibble(s[i*2+1]);
    if (hi < 0 || lo < 0) return -1;
    out[i] = (uint8_t)(hi << 4 | lo);
  }
  return (int)bytes;
}

} // namespace authmac

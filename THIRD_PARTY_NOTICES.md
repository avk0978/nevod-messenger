# Third-party components

Nevod's own code is licensed under the GNU AGPL-3.0 with an application store
exception (see [LICENSE](LICENSE)). The components below keep their own licenses.

## Bundled in this repository

| Component | Where | License |
|---|---|---|
| Ponomar Unicode font (`Ponomar-Regular.ttf`) — Slavonic Computing Initiative, https://github.com/slavonic/Ponomar | `ios/Nevod/Nevod/`, `ios/Nevod/SLKey/` | SIL Open Font License 1.1 — https://openfontlicense.org |

## Fetched at build time (not stored in this repository)

| Component | Used by | License |
|---|---|---|
| WebRTC (binary package https://github.com/stasel/WebRTC, built from https://webrtc.googlesource.com/src) | iOS app, calls | BSD 3-Clause + patent grant |
| cryptography | node | Apache-2.0 / BSD-3-Clause |
| msgpack | node | Apache-2.0 |
| websockets | node | BSD-3-Clause |
| aiosqlite | node | MIT |
| click | node | BSD-3-Clause |
| aiohttp | node | Apache-2.0 |
| PyJWT | node | MIT |
| httpx | node | BSD-3-Clause |

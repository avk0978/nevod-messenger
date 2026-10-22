# Nevod iOS

## Setup in Xcode

1. Open Xcode → File → New → Project → iOS App
2. Product Name: **Nevod**
3. Team: your Apple ID
4. Bundle ID: e.g. `com.yourname.nevod`
5. Interface: **SwiftUI**, Language: **Swift**
6. Save into this `ios/` folder — Xcode creates `Nevod.xcodeproj` here

7. In Xcode Project Navigator: right-click the **Nevod** group → Add Files to "Nevod"
8. Add all files from `Nevod/` (select all, make sure "Copy items if needed" is OFF)

9. Delete the auto-generated `ContentView.swift` — we have our own views.

## What's in each file

| File | Purpose |
|------|---------|
| `NevdApp.swift` | App entry point |
| `Protocol/MsgPack.swift` | msgpack encoder/decoder |
| `Crypto/BigUInt.swift` | Big integer for Schnorr mod-L arithmetic |
| `Crypto/CryptoManager.swift` | Ed25519, X25519, ChaCha20-Poly1305, Schnorr ZKP |
| `Protocol/NevdProtocol.swift` | Packet pack/unpack, signing |
| `Protocol/NevdClient.swift` | WebSocket client, auth, send/receive |
| `Storage/Models.swift` | Contact, Message, card parsing |
| `Storage/IdentityStore.swift` | Keychain + UserDefaults |
| `Storage/AppStore.swift` | Central state (ObservableObject) |
| `Views/*.swift` | SwiftUI UI |

## No external dependencies

Uses only: CryptoKit (built-in), Foundation, SwiftUI.

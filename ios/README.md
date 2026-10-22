# Nevod for iOS

SwiftUI app, iOS 17.2+. Three targets in `Nevod/Nevod.xcodeproj`:

| Target | What |
|---|---|
| `Nevod` | The app |
| `NotificationService` | Notification service extension — shows a neutral push text in the user's language; push payloads carry no message content |
| `SLKey` | Church Slavonic keyboard extension (see `Nevod/SLKEY_KEYBOARD.md`) |

## Building

1. Open `Nevod/Nevod.xcodeproj` in Xcode.
2. For each target, choose your team in *Signing & Capabilities* and change the bundle identifiers and the App Group (`group.com.avk.Nevod`) to your own.
3. Xcode fetches the only package dependency, [WebRTC](https://github.com/stasel/WebRTC), through Swift Package Manager.
4. Build and run on a device. Push notifications and VoIP calls need your own APNs key configured on the node you connect to.

The bundled node list (`Nevod/nodes.json`) and the curator-signed list of official accounts (`Nevod/official.json`) point to the public Nevod network.

## Layout

| Path | Purpose |
|---|---|
| `NevdApp.swift` | App entry point |
| `Crypto/` | Ed25519, X25519, ChaCha20-Poly1305 (CryptoKit), Schnorr ZKP, big-integer arithmetic |
| `Protocol/` | MessagePack, packet signing, WebSocket client, node browsing |
| `Storage/` | SwiftData models, identity in the Keychain, central app state, log, safety checks |
| `Call/` | CallKit + WebRTC voice calls |
| `Views/` | SwiftUI screens |
| `Localizable.xcstrings` | UI strings in 8 languages |
| `NodeManifest.swift` | Verification of the curator-signed bootstrap manifest |

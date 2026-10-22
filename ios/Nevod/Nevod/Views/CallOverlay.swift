import SwiftUI
import WebRTC
import AVKit

struct CallOverlay: View {
    @EnvironmentObject var callManager: CallManager

    var body: some View {
        Group {
            if callManager.state.isIdle {
                EmptyView()
            } else if callManager.isVideoCall {
                videoCallScreen
            } else {
                audioCallScreen
            }
        }
        .animation(.easeInOut(duration: 0.25), value: callManager.state.isIdle)
        // A call (incoming or outgoing) covers the whole screen, but the chat's text field
        // underneath keeps first responder — the keyboard stayed on top of the call screen.
        // Resign it whenever a call starts.
        .onChange(of: callManager.state.isIdle) { _, isIdle in
            if !isIdle { dismissKeyboard() }
        }
        .onAppear {
            if !callManager.state.isIdle { dismissKeyboard() }
        }
    }

    private func dismissKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder),
                                        to: nil, from: nil, for: nil)
    }

    // MARK: - Audio call (unchanged layout)

    @ViewBuilder
    private var audioCallScreen: some View {
        switch callManager.state {
        case .idle:
            EmptyView()
        case .incoming(let name, _):
            callScreen {
                Text(name).font(.title2.bold()).foregroundStyle(.white)
                Text("Входящий звонок").font(.subheadline).foregroundStyle(.white.opacity(0.7))
                Spacer()
                HStack(spacing: 64) {
                    CallActionButton(icon: "phone.down.fill", color: .red, label: "Отклонить") {
                        callManager.reject()
                    }
                    CallActionButton(icon: "phone.fill", color: .green, label: "Принять") {
                        callManager.accept()
                    }
                }
            }
        case .outgoing(let name, _):
            callScreen {
                Text(name).font(.title2.bold()).foregroundStyle(.white)
                Text("Устанавливаем соединение…")
                    .font(.subheadline).foregroundStyle(.white.opacity(0.7))
                Spacer()
                preConnectButtons
            }
        case .ringing(let name, _):
            callScreen {
                Text(name).font(.title2.bold()).foregroundStyle(.white)
                Text("Звоним…").font(.subheadline).foregroundStyle(.white.opacity(0.7))
                Spacer()
                preConnectButtons
            }
        case .connecting(let name, _):
            callScreen {
                Text(name).font(.title2.bold()).foregroundStyle(.white)
                Text("Соединение…").font(.subheadline).foregroundStyle(.white.opacity(0.7))
                Spacer()
                preConnectButtons
            }
        case .busy(let name):
            callScreen {
                Text(name).font(.title2.bold()).foregroundStyle(.white)
                Text("Абонент занят").font(.subheadline).foregroundStyle(.white.opacity(0.7))
                Spacer()
            }
        case .active(let name, _):
            callScreen {
                Text(name).font(.title2.bold()).foregroundStyle(.white)
                Text(durationString)
                    .font(.subheadline.monospacedDigit())
                    .foregroundStyle(.white.opacity(0.7))
                if let q = callManager.quality {
                    qualityBadge(q)
                }
                Spacer()
                // 5 buttons instead of the original 4 — shrunk (54pt vs 68pt) and tightened
                // (spacing 8, plus -16pt horizontal padding to claw back what callScreen's
                // shared 40pt padding takes) so they still fit on a narrow phone instead of
                // running off the right edge (confirmed cut off at 68pt/24pt-spacing, 2026-08-11).
                HStack(spacing: 8) {
                    CallActionButton(
                        icon: callManager.isMuted ? "mic.slash.fill" : "mic.fill",
                        color: callManager.isMuted ? .orange : .white.opacity(0.2),
                        label: callManager.isMuted ? "Вкл" : "Выкл",
                        size: 54
                    ) {
                        callManager.toggleMute()
                    }
                    CallActionButton(
                        icon: "speaker.wave.2.fill",
                        color: callManager.isSpeaker ? .blue : .white.opacity(0.2),
                        label: "Динамик",
                        size: 54
                    ) {
                        callManager.toggleSpeaker()
                    }
                    // Highlighted blue whenever the active route actually is Bluetooth — iOS
                    // auto-picks it as soon as a paired device is reachable, so this reflects
                    // "connected" without a separate, harder-to-keep-in-sync flag.
                    BluetoothButton(isActive: callManager.isBluetooth, size: 54)
                    // Turns this ongoing audio call into a video call — matches Telegram's
                    // own flow (start talking, tap the camera once you're already on the
                    // call) rather than a separate video-only entry point.
                    CallActionButton(icon: "video.fill", color: .white.opacity(0.2), label: "Видео", size: 54) {
                        callManager.enableVideoMidCall()
                    }
                    CallActionButton(icon: "phone.down.fill", color: .red, label: "Завершить", size: 54) {
                        callManager.hangup()
                    }
                }
                .padding(.horizontal, -16)
            }
        }
    }

    // Shown on .outgoing/.ringing/.connecting — lets the caller pick speaker/earpiece/
    // Bluetooth themselves *before* the callee answers, instead of being stuck with
    // startRingback()'s hardcoded loudspeaker default for the whole ringback period.
    // No video/camera button here — every call negotiates audio-only until .active (see
    // CallManager.startCall's doc comment), so there's nothing to toggle yet.
    @ViewBuilder
    private var preConnectButtons: some View {
        HStack(spacing: 8) {
            CallActionButton(
                icon: callManager.isMuted ? "mic.slash.fill" : "mic.fill",
                color: callManager.isMuted ? .orange : .white.opacity(0.2),
                label: callManager.isMuted ? "Вкл" : "Выкл",
                size: 54
            ) {
                callManager.toggleMute()
            }
            CallActionButton(
                icon: "speaker.wave.2.fill",
                color: callManager.isSpeaker ? .blue : .white.opacity(0.2),
                label: "Динамик",
                size: 54
            ) {
                callManager.toggleSpeaker()
            }
            BluetoothButton(isActive: callManager.isBluetooth, size: 54)
            CallActionButton(icon: "phone.down.fill", color: .red, label: "Завершить", size: 54) {
                callManager.hangup()
            }
        }
        .padding(.horizontal, 16)
    }

    // MARK: - Video call

    @ViewBuilder
    private var videoCallScreen: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            if let remote = callManager.remoteVideoTrack {
                RTCVideoRenderView(track: remote).ignoresSafeArea()
            } else {
                Image(systemName: "person.circle.fill")
                    .font(.system(size: 80))
                    .foregroundStyle(.white.opacity(0.3))
            }
            VStack {
                videoStatusHeader.padding(.top, 54)
                Spacer()
                if !callManager.isCameraOff, let local = callManager.localVideoTrack {
                    HStack {
                        Spacer()
                        RTCVideoRenderView(track: local, mirror: callManager.isFrontCamera)
                            .frame(width: 96, height: 130)
                            .clipShape(RoundedRectangle(cornerRadius: 14))
                            .overlay(RoundedRectangle(cornerRadius: 14).stroke(.white.opacity(0.3), lineWidth: 1))
                            .padding(.trailing, 16)
                    }
                }
                videoButtonsRow.padding(.bottom, 44).padding(.top, 12)
            }
        }
    }

    @ViewBuilder
    private var videoStatusHeader: some View {
        VStack(spacing: 4) {
            if let name = callManager.state.contactName {
                Text(name).font(.title3.bold()).foregroundStyle(.white)
            }
            Text(videoStatusText).font(.caption).foregroundStyle(.white.opacity(0.85))
            if case .active = callManager.state, let q = callManager.quality {
                qualityBadge(q)
            }
        }
        .padding(.horizontal, 14).padding(.vertical, 8)
        .background(.black.opacity(0.35))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var videoStatusText: String {
        switch callManager.state {
        case .idle: return ""
        case .incoming: return String(localized: "Входящий видеозвонок")
        case .outgoing: return String(localized: "Устанавливаем соединение…")
        case .ringing: return String(localized: "Звоним…")
        case .connecting: return String(localized: "Соединение…")
        case .active: return durationString
        case .busy: return String(localized: "Абонент занят")
        }
    }

    @ViewBuilder
    private var videoButtonsRow: some View {
        switch callManager.state {
        case .idle, .busy:
            EmptyView()
        case .incoming:
            HStack(spacing: 64) {
                CallActionButton(icon: "phone.down.fill", color: .red, label: "Отклонить") {
                    callManager.reject()
                }
                CallActionButton(icon: "video.fill", color: .green, label: "Принять") {
                    callManager.accept()
                }
            }
        case .outgoing, .ringing, .connecting:
            // Unreachable in practice — every call negotiates audio-only until .active (see
            // CallManager.startCall's doc comment), so isVideoCall is always false here and
            // audioCallScreen's preConnectButtons is what actually renders pre-connect.
            CallActionButton(icon: "phone.down.fill", color: .red, label: "Завершить") {
                callManager.hangup()
            }
        case .active:
            // Shrunk to 54pt/8pt spacing to fit the now-5-button row — same sizing as the
            // audio call screen's row, for the same reason (see its own comment).
            HStack(spacing: 8) {
                CallActionButton(
                    icon: callManager.isMuted ? "mic.slash.fill" : "mic.fill",
                    color: callManager.isMuted ? .orange : .white.opacity(0.2),
                    label: callManager.isMuted ? "Вкл" : "Выкл",
                    size: 54
                ) {
                    callManager.toggleMute()
                }
                BluetoothButton(isActive: callManager.isBluetooth, size: 54)
                CallActionButton(
                    icon: (callManager.localVideoTrack == nil || callManager.isCameraOff) ? "video.slash.fill" : "video.fill",
                    color: (callManager.localVideoTrack == nil || callManager.isCameraOff) ? .orange : .white.opacity(0.2),
                    label: (callManager.localVideoTrack == nil || callManager.isCameraOff) ? "Вкл" : "Выкл",
                    size: 54
                ) {
                    // We may be on this screen purely because the PEER's video arrived — our
                    // own camera might never have been turned on, in which case this
                    // button's job is to start it (enableVideoMidCall), not mute an
                    // already-running one (toggleCameraEnabled).
                    if callManager.localVideoTrack == nil {
                        callManager.enableVideoMidCall()
                    } else {
                        callManager.toggleCameraEnabled()
                    }
                }
                CallActionButton(
                    icon: "arrow.triangle.2.circlepath.camera.fill",
                    color: .white.opacity(0.2),
                    label: "Камера",
                    size: 54
                ) {
                    callManager.toggleCamera()
                }
                CallActionButton(icon: "phone.down.fill", color: .red, label: "Завершить", size: 54) {
                    callManager.hangup()
                }
            }
        }
    }

    // MARK: - Shared

    private var durationString: String {
        let s = callManager.callDuration
        let h = s / 3600, m = (s % 3600) / 60, sec = s % 60
        return h > 0
            ? String(format: "%d:%02d:%02d", h, m, sec)
            : String(format: "%d:%02d", m, sec)
    }

    @ViewBuilder
    private func qualityBadge(_ q: CallQuality) -> some View {
        HStack(spacing: 6) {
            Circle()
                .fill(q == .good ? Color.green : q == .medium ? Color.yellow : Color.red)
                .frame(width: 8, height: 8)
            Text(q == .good ? String(localized: "Хорошее") : q == .medium ? String(localized: "Среднее") : String(localized: "Плохое"))
                .font(.caption)
                .foregroundStyle(.white.opacity(0.65))
        }
        .padding(.top, 4)
    }

    @ViewBuilder
    private func callScreen<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        ZStack {
            Color.black.opacity(0.88).ignoresSafeArea()
            VStack(spacing: 16) {
                Spacer()
                Image(systemName: "person.circle.fill")
                    .font(.system(size: 80))
                    .foregroundStyle(.white.opacity(0.3))
                    .padding(.bottom, 8)
                content()
                Spacer().frame(height: 48)
            }
            .padding(.horizontal, 40)
        }
    }
}

private struct CallActionButton: View {
    let icon: String
    let color: Color
    // LocalizedStringKey, not String — a plain String goes into Text() verbatim and is never
    // looked up in Localizable.xcstrings, which left every call-screen button label Russian
    // regardless of the phone's language.
    let label: LocalizedStringKey
    var size: CGFloat = 68
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                ZStack {
                    Circle().fill(color).frame(width: size, height: size)
                    Image(systemName: icon).font(.title2).foregroundStyle(.white)
                }
                Text(label).font(.caption).foregroundStyle(.white.opacity(0.8))
            }
        }
    }
}

// MARK: - Bluetooth button — real system route menu (Bluetooth/AirPlay/speaker/earpiece)

/// Same look as a plain CallActionButton, but the actual tap target is a real, fully
/// interactive AVRoutePickerView layered on top — tinted clear so only our own icon/circle
/// underneath is visible, but real touches land on it, so it opens Apple's own output-route
/// menu exactly like tapping it anywhere else in iOS would. This is the only API that can
/// show that menu at all (no way to enumerate or pick a specific route manually via
/// AVAudioSession), and it must be a genuine touch — no programmatic "just show the menu"
/// call exists (confirmed the hard way 2026-08-11: a synthetic sendActions() trigger made the
/// menu appear, but selecting a device inside it flapped the route back and forth instead of
/// sticking).
private struct BluetoothButton: View {
    let isActive: Bool
    var size: CGFloat = 68

    var body: some View {
        VStack(spacing: 8) {
            ZStack {
                Circle().fill(isActive ? Color.blue : Color.white.opacity(0.2)).frame(width: size, height: size)
                Image(systemName: "dot.radiowaves.left.and.right").font(.title2).foregroundStyle(.white)
                    .allowsHitTesting(false)
                RoutePickerRepresentable()
                    .frame(width: size, height: size)
                    .clipShape(Circle())
            }
            Text("Bluetooth").font(.caption).foregroundStyle(.white.opacity(0.8))
        }
    }
}

private struct RoutePickerRepresentable: UIViewRepresentable {
    func makeUIView(context: Context) -> AVRoutePickerView {
        let view = AVRoutePickerView()
        view.tintColor = .clear
        view.activeTintColor = .clear
        view.backgroundColor = .clear
        view.prioritizesVideoDevices = false
        return view
    }

    func updateUIView(_ uiView: AVRoutePickerView, context: Context) {}
}

// MARK: - RTCVideoTrack renderer

/// Wraps WebRTC's Metal-backed video view. `mirror` flips it horizontally for the local
/// front-camera preview (matches every other camera app — otherwise your own preview looks
/// backwards, though the frames sent to the peer are never actually mirrored).
private struct RTCVideoRenderView: UIViewRepresentable {
    let track: RTCVideoTrack?
    var mirror: Bool = false

    func makeUIView(context: Context) -> RTCMTLVideoView {
        let view = RTCMTLVideoView()
        view.videoContentMode = .scaleAspectFill
        return view
    }

    func updateUIView(_ uiView: RTCMTLVideoView, context: Context) {
        uiView.transform = mirror ? CGAffineTransform(scaleX: -1, y: 1) : .identity
        context.coordinator.attach(track: track, to: uiView)
    }

    func makeCoordinator() -> Coordinator { Coordinator() }

    final class Coordinator {
        private weak var currentTrack: RTCVideoTrack?
        func attach(track: RTCVideoTrack?, to view: RTCMTLVideoView) {
            guard currentTrack !== track else { return }
            currentTrack?.remove(view)
            currentTrack = track
            track?.add(view)
        }
    }
}

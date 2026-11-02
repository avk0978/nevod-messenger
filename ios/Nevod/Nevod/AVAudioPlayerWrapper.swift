import AVFoundation

/// Voice message playback. Takes the app's audio session only when no call is going on and
/// gives it back when playback ends (audit 2026-11-02, А2): it used to switch the session to
/// .playback, activate it and never deactivate it — a session the app holds itself is what
/// CallKit may skip activating for the next call, and during a call the category switch broke
/// the call's own audio.
@MainActor
final class AVAudioPlayerWrapper: NSObject, AVAudioPlayerDelegate {
    private var player: AVAudioPlayer?
    private let onFinish: () -> Void
    private var activatedSession = false

    init?(data: Data, onFinish: @escaping () -> Void) {
        self.onFinish = onFinish
        super.init()
        do {
            if NevdClient.callInProgress {
                // The call owns the session (CallKit activated it) — play through it as is.
                nlog("voicePlayer during a call — session left to the call: \(AudioDiag.snapshot())")
            } else {
                nlog("voicePlayer activating session (playback) before: \(AudioDiag.snapshot())")
                try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
                try AVAudioSession.sharedInstance().setActive(true)
                activatedSession = true
            }
            player = try AVAudioPlayer(data: data)
            player?.delegate = self
        } catch {
            nlog("voicePlayer session/player FAILED err=\(error)")
            releaseSession()
            return nil
        }
    }

    func play()  { nlog("voicePlayer play"); player?.play() }
    func stop()  { nlog("voicePlayer stop"); player?.stop(); releaseSession() }

    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        MainActor.assumeIsolated {
            nlog("voicePlayer finished ok=\(flag)")
            releaseSession()
            onFinish()
        }
    }

    /// Gives the session back — unless a call started meanwhile: CallKit owns it then.
    private func releaseSession() {
        guard activatedSession else { return }
        activatedSession = false
        guard !NevdClient.callInProgress else {
            nlog("voicePlayer ended during a call — session left to the call")
            return
        }
        do {
            try AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
            nlog("voicePlayer session released: \(AudioDiag.snapshot())")
        } catch {
            nlog("voicePlayer session release FAILED err=\(error)")
        }
    }
}

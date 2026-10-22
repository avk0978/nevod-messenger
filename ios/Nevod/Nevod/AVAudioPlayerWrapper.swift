import AVFoundation

final class AVAudioPlayerWrapper: NSObject, AVAudioPlayerDelegate {
    private var player: AVAudioPlayer?
    private let onFinish: () -> Void

    init?(data: Data, onFinish: @escaping () -> Void) {
        self.onFinish = onFinish
        super.init()
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
            try AVAudioSession.sharedInstance().setActive(true)
            player = try AVAudioPlayer(data: data)
            player?.delegate = self
        } catch {
            return nil
        }
    }

    func play()  { player?.play() }
    func stop()  { player?.stop() }

    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        onFinish()
    }
}

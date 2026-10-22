import Foundation
import os
import Darwin

/// Lightweight append-only file logger. Thread-safe. Survives app restarts.
/// Log file: Documents/nevod.log — mailed to support via Profile → Диагностика (DiagnosticsView).
final class NevLogger {
    static let shared = NevLogger()

    private let fileURL: URL
    private let queue = DispatchQueue(label: "nevod.logger", qos: .userInitiated)
    private var handle: FileHandle?
    // Redundant channel that doesn't depend on the file write succeeding — the SLKey extension's
    // lines never once reached the shared log file even across repeated opens, so file-based
    // diagnosis alone hit a dead end. This mirrors every line into the unified system log,
    // visible via Console.app (or Xcode ▸ Window ▸ Devices and Simulators ▸ Open Console) filtered
    // to process "SLKey" on the connected device — works even if App Group file access is broken.
    private let osLogger = Logger(subsystem: "com.avk.Nevod", category: "nevod")

    var logFileURL: URL { fileURL }

    private init() {
        // Shared App Group container (not the host app's own private Documents) — so the
        // SLKey keyboard extension, a SEPARATE sandboxed process with no access to Nevod's own
        // container, can append to the exact same file. Falls back to the app's own Documents
        // if the App Group entitlement isn't wired up yet (e.g. before the Xcode capability is
        // added) — better a working log in the wrong place than a crash on nil.
        let groupContainer = FileManager.default
            .containerURL(forSecurityApplicationGroupIdentifier: "group.com.avk.Nevod")
        let docs = groupContainer
            ?? FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        fileURL = docs.appendingPathComponent("nevod.log")

        // Rotate when file exceeds 3 MB — keep previous session logs intact otherwise
        if let size = try? fileURL.resourceValues(forKeys: [.fileSizeKey]).fileSize, size > 3_000_000 {
            try? FileManager.default.removeItem(at: fileURL)
        }
        // Create only if absent — NEVER truncate existing content
        if !FileManager.default.fileExists(atPath: fileURL.path) {
            FileManager.default.createFile(atPath: fileURL.path, contents: nil)
        }
        handle = try? FileHandle(forWritingTo: fileURL)
        handle?.seekToEndOfFile()
        // Diagnostic for whether the App Group container resolved — the SLKey extension is a
        // separate process; if its entitlement/provisioning isn't actually wired up despite the
        // .entitlements file looking correct, containerURL(forSecurityApplicationGroupIdentifier:)
        // silently returns nil and this logger falls back to the extension's own private sandbox,
        // which no one ever reads. Confirmed via a real device log spanning a full day of keyboard
        // use: zero SLKey-tagged lines ever reached the shared file — this line tells us which.
        syncWrite("─── session start [\(hms())] ─── groupContainer=\(groupContainer != nil ? "ok" : "NIL-fallback-to-private-sandbox")\n")
    }

    func log(_ msg: String, file: String = #fileID, line: Int = #line) {
        let tag = URL(fileURLWithPath: file).deletingPathExtension().lastPathComponent
        let entry = "[\(hms())] [\(memMB())MB] \(tag):\(line) \(msg)\n"
        // Synchronous: guarantees write to disk before the next line of caller runs.
        // Logger queue is never called from itself, so no deadlock.
        queue.sync { self.syncWrite(entry) }
    }

    func clear() {
        queue.sync {
            self.handle?.truncateFile(atOffset: 0)
            self.handle?.seekToEndOfFile()
        }
    }

    private func syncWrite(_ s: String) {
        // .error level + explicit .public privacy: persisted to disk and shown in Console.app
        // without needing "Include Debug/Info Messages" toggled on, and without the message text
        // being redacted as "<private>" (the default for interpolated strings in os.Logger).
        osLogger.error("\(s, privacy: .public)")
        guard let data = s.data(using: .utf8) else { return }
        // Re-seek before every write: this file is shared across two independent OS processes
        // (main app + SLKey extension), each holding its own FileHandle with its own internally
        // tracked offset. Without reseeking, a handle only knows the file's true length as of
        // whenever IT last opened/seeked — a second process appending in between causes this
        // handle's next write to land at its stale offset and clobber what the other process
        // just wrote, rather than actually appending after it.
        handle?.seekToEndOfFile()
        handle?.write(data)
    }

    private func hms() -> String {
        let c = Calendar.current.dateComponents([.hour, .minute, .second, .nanosecond], from: Date())
        let ms = (c.nanosecond ?? 0) / 1_000_000
        return String(format: "%02d:%02d:%02d.%03d", c.hour ?? 0, c.minute ?? 0, c.second ?? 0, ms)
    }

    /// Current resident footprint (what Xcode's memory gauge / iOS jetsam accounting actually
    /// uses), NOT ru_maxrss — that's a lifetime high-water mark that can only ever go up within
    /// a process, which made every past log read as "memory never comes back down after a call"
    /// regardless of whether it actually did. phys_footprint via TASK_VM_INFO is Apple's own
    /// documented way to read live memory use (see "Understanding your app's memory footprint,"
    /// WWDC18/2018).
    private func memMB() -> Int {
        var info = task_vm_info_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<task_vm_info_data_t>.size / MemoryLayout<integer_t>.size)
        let result = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count)
            }
        }
        guard result == KERN_SUCCESS else { return 0 }
        return Int(info.phys_footprint / 1_048_576)
    }
}

/// Global shortcut — `nlog("message")` from any file.
func nlog(_ msg: String, file: String = #fileID, line: Int = #line) {
    NevLogger.shared.log(msg, file: file, line: line)
}

import AVFoundation
import Foundation

print("Requesting microphone access...")
AVCaptureDevice.requestAccess(for: .audio) { granted in
    if granted {
        print("Microphone access GRANTED")
    } else {
        print("Microphone access DENIED - go to System Settings > Privacy & Security > Microphone")
    }
    exit(0)
}
RunLoop.main.run(until: Date(timeIntervalSinceNow: 30))

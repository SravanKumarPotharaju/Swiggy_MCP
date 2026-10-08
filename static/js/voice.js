// SmartFlow Voice Assistant Module — Continuous Hands-Free Voice Mode
class VoiceAssistant {
  constructor(onTranscriptCallback, onStateChangeCallback, onExitCallback) {
    this.onTranscript = onTranscriptCallback;
    this.onStateChange = onStateChangeCallback;
    this.onExit = onExitCallback;
    this.recognition = null;
    this.isListening = false;
    this.keepListening = false;
    this.ttsEnabled = false; // Strictly muted as requested ("donot read the response message")
    this.restartTimeout = null;

    this.initRecognition();
  }

  initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Web Speech API is not supported in this browser.');
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = false; // Turn-based with auto-rearm is far more stable across browsers
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-IN'; // Indian English / Hindi mix

    this.recognition.onstart = () => {
      this.isListening = true;
      if (this.onStateChange) this.onStateChange(true);
    };

    this.recognition.onresult = (event) => {
      if (!event.results || !event.results[0]) return;
      const transcript = event.results[0][0].transcript.trim();
      console.log('Voice recognized:', transcript);

      const lower = transcript.toLowerCase();
      // Check for exit keywords
      if (
        lower === 'exit' ||
        lower === 'stop' ||
        lower === 'quit' ||
        lower === 'bye' ||
        lower === 'cancel' ||
        lower === 'exit session' ||
        lower.endsWith(' exit') ||
        lower.startsWith('exit ')
      ) {
        console.log('Exit keyword detected. Stopping voice session.');
        this.stopListening();
        if (this.onExit) this.onExit(transcript);
        return;
      }

      if (this.onTranscript) {
        this.onTranscript(transcript);
      }
    };

    this.recognition.onerror = (event) => {
      console.warn('Speech recognition event:', event.error);
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        this.keepListening = false;
        this.isListening = false;
        if (this.onStateChange) this.onStateChange(false);
      }
      // For 'no-speech' or other minor events, onend will automatically re-arm if keepListening is true
    };

    this.recognition.onend = () => {
      this.isListening = false;
      if (this.keepListening) {
        // Continuous mode: automatically resume listening so user can talk again!
        clearTimeout(this.restartTimeout);
        this.restartTimeout = setTimeout(() => {
          if (this.keepListening) {
            try {
              this.recognition.start();
            } catch (e) {
              console.log('Recognition restart status:', e.message);
            }
          }
        }, 300);
      } else {
        if (this.onStateChange) this.onStateChange(false);
      }
    };
  }

  startListening() {
    this.keepListening = true;
    if (!this.recognition) return;
    try {
      this.recognition.start();
    } catch (e) {
      console.log('Already listening:', e.message);
    }
  }

  stopListening() {
    this.keepListening = false;
    clearTimeout(this.restartTimeout);
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }
    this.isListening = false;
    if (this.onStateChange) this.onStateChange(false);
  }

  toggleListening() {
    if (this.keepListening || this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  speak(text) {
    // Intentionally muted per user requirement:
    // "after response donot read the response message"
    if (!this.ttsEnabled) return;
  }
}

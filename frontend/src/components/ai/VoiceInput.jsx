/**
 * Voice Input Component for AI Assistant
 * Uses Web Speech API for speech-to-text
 */

import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';

const VoiceInput = ({ onTranscript, language = 'en-US' }) => {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [interimTranscript, setInterimTranscript] = useState('');
    const [isSupported, setIsSupported] = useState(true);
    const recognitionRef = useRef(null);

    useEffect(() => {
        // Check if browser supports Web Speech API
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            setIsSupported(false);
            return;
        }

        // Initialize speech recognition
        const recognition = new SpeechRecognition();
        recognition.continuous = false; // Stop after one result
        recognition.interimResults = true;
        recognition.lang = language;

        recognition.onresult = (event) => {
            let interimText = '';
            let finalText = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcriptPiece = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalText += transcriptPiece;
                } else {
                    interimText += transcriptPiece;
                }

            }
            setInterimTranscript(interimText);

            if (finalText) {
                const newTranscript = transcript + finalText;
                setTranscript(newTranscript);
                if (onTranscript) {
                    onTranscript(newTranscript);
                }
                setIsListening(false);
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            setIsListening(false);
        };

        recognition.onend = () => {
            setIsListening(false);
        };

        recognitionRef.current = recognition;

        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
        }
    }, [language, transcript, onTranscript]);

    const toggleListening = () => {
        if (!recognitionRef.current) return;

        if (isListening) {
            recognitionRef.current.stop();
            setIsListening(false);
        } else {
            setTranscript('');
            setInterimTranscript('');
            recognitionRef.current.start();
            setIsListening(true);
        }
    };
    return (

        <button
            onClick={toggleListening}
            disabled={!isSupported}
            className={`p-2.5 rounded-lg transition-all flex items-center justify-center shrink-0 ${
                !isSupported
                    ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed opacity-50'
                    : isListening
                    ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/50 animate-pulse'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
            title={!isSupported ? 'Voice input not supported in this browser' : isListening ? 'Stop recording' : 'Start voice input'}
        >
            {isListening ? <MicOff size={18} /> : <Mic size={18} />}
        </button>
    );
};

export default VoiceInput;

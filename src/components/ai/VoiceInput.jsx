/**
 * Voice Input Component for AI Assistant
 * Uses Web Speech API for speech-to-text
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
        };
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

    if (!isSupported) {
        return (
            <div className="text-xs text-muted-foreground">
                Voice input not supported in this browser
            </div>
        );
    }

    return (
        <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleListening}
            className={`p-3 rounded-lg transition-all flex items-center gap-2 ${isListening
                    ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/50 animate-pulse'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
            title={isListening ? 'Stop recording' : 'Start voice input'}
        >
            {isListening ? <MicOff size={20} /> : <Mic size={20} />}
            <AnimatePresence>
                {isListening && (
                    <motion.span
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: 'auto' }}
                        exit={{ opacity: 0, width: 0 }}
                        className="text-sm font-medium whitespace-nowrap overflow-hidden"
                    >
                        {interimTranscript || 'Listening...'}
                    </motion.span>
                )}
            </AnimatePresence>
        </motion.button>
    );
};

export default VoiceInput;

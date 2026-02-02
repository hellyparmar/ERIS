/**
 * Voice Input Component for AI Assistant
 * Uses Web Speech API for speech-to-text
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Volume2 } from 'lucide-react';

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
        recognition.continuous = true;
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
            <div className="text-xs text-gray-500 dark:text-gray-400">
                Voice input not supported in this browser
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={toggleListening}
                    className={`p-3 rounded-full transition-all ${isListening
                            ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/50'
                            : 'bg-blue-500 hover:bg-blue-600 text-white'
                        }`}
                    title={isListening ? 'Stop recording' : 'Start voice input'}
                >
                    {isListening ? <MicOff size={20} /> : <Mic size={20} />}
                </motion.button>

                <AnimatePresence>
                    {isListening && (
                        <motion.div
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -10 }}
                            className="flex items-center gap-2 text-red-500"
                        >
                            <Volume2 size={16} className="animate-pulse" />
                            <span className="text-sm font-medium">Listening...</span>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <AnimatePresence>
                {(transcript || interimTranscript) && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg"
                    >
                        <p className="text-sm text-gray-900 dark:text-white">
                            {transcript}
                            <span className="text-gray-400 dark:text-gray-500">{interimTranscript}</span>
                        </p>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default VoiceInput;

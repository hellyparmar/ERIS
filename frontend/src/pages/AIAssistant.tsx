import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

interface Message {
  id: string
  text: string
  sender: 'user' | 'assistant'
  timestamp: string
}

const AIAssistant: React.FC = () => {
  const [messages, setMessages] = React.useState<Message[]>([
    { id: '1', text: 'Hello! I\'m your retail assistant. How can I help you today?', sender: 'assistant', timestamp: '10:30 AM' },
  ])
  const [input, setInput] = React.useState('')
  const [isTyping, setIsTyping] = React.useState(false)

  const handleSend = () => {
    if (!input.trim()) return

    setMessages([...messages, { id: Date.now().toString(), text: input, sender: 'user', timestamp: new Date().toLocaleTimeString() }])
    setInput('')
    setIsTyping(true)

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          text: 'This is a sample response from the AI assistant. In production, this would connect to your smart-chat API endpoint.',
          sender: 'assistant',
          timestamp: new Date().toLocaleTimeString(),
        },
      ])
      setIsTyping(false)
    }, 1000)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">AI Assistant</h1>
        <p className="text-gray-600 mt-1">Chat with your intelligent retail assistant</p>
      </div>

      <Card className="flex flex-col h-[600px]">
        <CardHeader>
          <CardTitle>Conversation</CardTitle>
          <CardDescription>Ask questions about sales, inventory, forecasts, and more</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto flex flex-col">
          <div className="space-y-4 flex-1">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-xs px-4 py-2 rounded-lg ${
                    message.sender === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p>{message.text}</p>
                  <span className="text-xs mt-1 block opacity-70">{message.timestamp}</span>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-4 py-2 rounded-lg">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>

        <div className="border-t p-6">
          <div className="space-y-3">
            <div className="mb-4">
              <h4 className="text-sm font-semibold mb-2">Quick Suggestions:</h4>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="secondary" size="sm" onClick={() => setInput('What were sales last week?')}>
                  Last week sales
                </Button>
                <Button variant="secondary" size="sm" onClick={() => setInput('Which products are low in stock?')}>
                  Low stock items
                </Button>
                <Button variant="secondary" size="sm" onClick={() => setInput('Forecast for next week')}>
                  Next week forecast
                </Button>
                <Button variant="secondary" size="sm" onClick={() => setInput('Top performing outlet')}>
                  Top outlet
                </Button>
              </div>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Type your question..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <Button onClick={handleSend} disabled={isTyping || !input.trim()}>
                Send
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default AIAssistant

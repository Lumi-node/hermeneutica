import { useState, useCallback } from 'react';

type Status = 'idle' | 'sending' | 'sent' | 'error';

export function ContactForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState<Status>('idle');

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !message.trim()) return;

    setStatus('sending');
    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), email: email.trim(), message: message.trim() }),
      });
      if (res.ok) {
        setStatus('sent');
        setName('');
        setEmail('');
        setMessage('');
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }
  }, [name, email, message]);

  if (status === 'sent') {
    return (
      <div className="bg-accent-green/10 border border-accent-green/20 rounded-lg p-6 text-center">
        <div className="text-accent-green text-lg mb-2">Message sent!</div>
        <p className="text-sm text-gray-400">Thank you for reaching out. We'll get back to you soon.</p>
        <button
          onClick={() => setStatus('idle')}
          className="mt-4 text-xs text-gray-500 hover:text-white transition underline"
        >
          Send another message
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid sm:grid-cols-2 gap-3">
        <div>
          <label className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full bg-white/5 text-white text-sm rounded-lg px-3 py-2 border border-white/10 focus:border-accent-blue outline-none transition"
            placeholder="Your name"
          />
        </div>
        <div>
          <label className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full bg-white/5 text-white text-sm rounded-lg px-3 py-2 border border-white/10 focus:border-accent-blue outline-none transition"
            placeholder="you@example.com"
          />
        </div>
      </div>
      <div>
        <label className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Message</label>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          required
          rows={4}
          className="w-full bg-white/5 text-white text-sm rounded-lg px-3 py-2 border border-white/10 focus:border-accent-blue outline-none transition resize-none"
          placeholder="Your message, feedback, or questions..."
        />
      </div>
      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={status === 'sending'}
          className="bg-accent-blue hover:bg-accent-blue/80 disabled:opacity-50 text-white text-sm px-5 py-2 rounded-lg transition"
        >
          {status === 'sending' ? 'Sending...' : 'Send Message'}
        </button>
        {status === 'error' && (
          <span className="text-xs text-red-400">Failed to send. Please try again.</span>
        )}
      </div>
    </form>
  );
}

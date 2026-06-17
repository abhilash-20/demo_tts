import { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { supabase } from '../lib/supabase';
import axios from 'axios';

interface TextInputProps {
  onGenerationStart?: () => void;
}

export function TextInput({ onGenerationStart }: TextInputProps) {
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!title.trim() || !text.trim()) {
      setError('Please provide both a title and text content');
      return;
    }

    if (text.length < 10) {
      setError('Text must be at least 10 characters long');
      return;
    }

    setIsLoading(true);

  //   try {
  //     const { data, error: insertError } = await supabase
  //       .from('audiobook_generations')
  //       .insert({
  //         title: title.trim(),
  //         input_text: text.trim(),
  //         input_method: 'text',
  //         status: 'pending',
  //       })
  //       .select()
  //       .maybeSingle();

  //     if (insertError) throw insertError;

  //     if (data) {
  //       setTitle('');
  //       setText('');
  //       if (onGenerationStart) onGenerationStart();
  //     }
  //   } catch (err) {
  //     setError(err instanceof Error ? err.message : 'Failed to submit text');
  //   } finally {
  //     setIsLoading(false);
  //   }
  // };

    try {
      const formData = new FormData();
      
      formData.append('title', title);
      formData.append('text', text); // 👈 MUST match: text: str = Form(...)

      const response = await axios.post(
        'http://localhost:8000/paste-text/',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 1)
            );
            console.log(`Upload progress: ${percentCompleted}%`);
          },
        }
      );

      console.log('Text processed:', response.data);

      // Reset UI
      setTitle('');
      setText('');
      if (onGenerationStart) onGenerationStart();

    } catch (err: any) {
      setError(
        err.response?.data?.error ||
        err.message ||
        'Failed to submit text'
      );
    } finally {
      setIsLoading(false);
    }

  };

  const characterCount = text.length;
  const wordCount = text.trim().split(/\s+/).filter(Boolean).length;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="title" className="block text-sm font-semibold text-gray-700 mb-2">
          Audiobook Title
        </label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter a title for your audiobook..."
          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-900 placeholder-gray-400"
          disabled={isLoading}
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label htmlFor="text" className="block text-sm font-semibold text-gray-700">
            Your Text Content
          </label>
          <div className="flex gap-4 text-xs text-gray-500">
            <span>{characterCount} characters</span>
            <span>{wordCount} words</span>
          </div>
        </div>
        <textarea
          id="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste or type your text here. The text will be converted into a natural-sounding audiobook..."
          rows={12}
          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none text-gray-900 placeholder-gray-400"
          disabled={isLoading}
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading || !title.trim() || !text.trim()}
        className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold py-4 px-6 rounded-xl hover:from-blue-700 hover:to-cyan-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 shadow-lg hover:shadow-xl"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating Audiobook...
          </>
        ) : (
          <>
            <Send className="w-5 h-5" />
            Generate Audiobook
          </>
        )}
      </button>
    </form>
  );
}
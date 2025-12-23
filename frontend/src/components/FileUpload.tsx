import { useState, useRef } from 'react';
import { Upload, File, X, Loader2, Send } from 'lucide-react';
import { supabase } from '../lib/supabase';
import axios from 'axios';

interface FileUploadProps {
  onGenerationStart?: () => void;
}

export function FileUpload({ onGenerationStart }: FileUploadProps) {
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [fileContent, setFileContent] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileRead = async (selectedFile: File) => {
    if (!selectedFile.name.endsWith('.pdf')) {
      setError('Please upload a .pdf file');
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    try {
      const text = await selectedFile.text();
      setFileContent(text);
      setFile(selectedFile);
      setError('');
    } catch (err) {
      setError('Failed to read file');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileRead(droppedFile);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileRead(selectedFile);
    }
  };

  const removeFile = () => {
    setFile(null);
    setFileContent('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!title.trim() || !file) {
      setError('Please provide both a title and upload a file');
      return;
    }

    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('file', file); // file is of type File from <input type="file" />

      const response = await axios.post(
        'http://localhost:8000/upload-pdf/',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 1)
            );
            console.log(`Upload progress: ${percentCompleted}%`);
          },
        }
      );

      console.log('PDF processed:', response.data);
      // response.data contains: characters_detected, text_length, audiobook_file, generation_time_seconds, message

      // Reset form
      setTitle('');
      removeFile();
      if (onGenerationStart) onGenerationStart();

    } catch (err: any) {
      setError(
        err.response?.data?.error ||
        err.message ||
        'Failed to submit file'
      );
    } finally {
      setIsLoading(false);
    }
  };


  const characterCount = fileContent.length;
  const wordCount = fileContent.trim().split(/\s+/).filter(Boolean).length;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="file-title" className="block text-sm font-semibold text-gray-700 mb-2">
          Audiobook Title
        </label>
        <input
          type="text"
          id="file-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter a title for your audiobook..."
          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-900 placeholder-gray-400"
          disabled={isLoading}
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Upload Text File
        </label>

        {!file ? (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
              isDragging
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
            }`}
          >
            <Upload className={`w-12 h-12 mx-auto mb-4 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`} />
            <p className="text-lg font-medium text-gray-700 mb-2">
              Drop your text file here
            </p>
            <p className="text-sm text-gray-500 mb-4">or click to browse</p>
            <p className="text-xs text-gray-400">Supports .pdf files up to 10MB</p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        ) : (
          <div className="border border-gray-300 rounded-xl p-6 bg-gradient-to-r from-blue-50 to-cyan-50">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="bg-blue-600 p-2 rounded-lg">
                  <File className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-500">
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={removeFile}
                className="text-gray-400 hover:text-red-500 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex gap-4 text-xs text-gray-600 bg-white px-3 py-2 rounded-lg">
              <span>{characterCount} characters</span>
              <span>{wordCount} words</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading || !title.trim() || !file}
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
import { useState } from 'react';
import { FileText, Type } from 'lucide-react';
import { TextInput } from './TextInput';
import { FileUpload } from './FileUpload';

export function InputMethods() {
  const [activeTab, setActiveTab] = useState<'text' | 'file'>('text');

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-100">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('text')}
            className={`flex-1 flex items-center justify-center gap-3 px-8 py-6 text-lg font-semibold transition-all ${
              activeTab === 'text'
                ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Type className="w-6 h-6" />
            Write Text
          </button>
          <button
            onClick={() => setActiveTab('file')}
            className={`flex-1 flex items-center justify-center gap-3 px-8 py-6 text-lg font-semibold transition-all ${
              activeTab === 'file'
                ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <FileText className="w-6 h-6" />
            Upload File
          </button>
        </div>

        <div className="p-8">
          {activeTab === 'text' ? <TextInput /> : <FileUpload />}
        </div>
      </div>
    </div>
  );
}
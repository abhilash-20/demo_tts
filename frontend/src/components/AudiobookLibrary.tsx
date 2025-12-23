import { useState, useEffect } from 'react';
import { Library, Clock, Calendar, FileText, Upload, Loader2, Play, AlertCircle } from 'lucide-react';
import { supabase } from '../lib/supabase';
import type { AudiobookGeneration } from '../lib/database.types';

const sampleGenerations: AudiobookGeneration[] = [
  {
    "id": "c1a8b2f4-4f7d-4b6b-9c63-91cdd6f5a101",
    "title": "Introduction to Distributed Systems",
    "input_text": "A distributed system is a collection of independent computers that appears to its users as a single coherent system. This audiobook explains the fundamental concepts, challenges, and design principles involved in building scalable distributed systems.",
    "input_method": "file",
    "file_name": "distributed_systems_intro.pdf",
    "audio_url": "https://your-supabase-bucket.supabase.co/storage/v1/object/public/audiobooks/distributed_systems_intro.mp3",
    "duration": 742,
    "status": "completed",
    "error_message": null,
    "created_at": "2025-12-21T10:15:00.000Z",
    "updated_at": "2025-12-21T10:15:00.000Z"
  },
  {
    "id": "d3f6e9c2-2d44-41f4-9d1a-4e9f8a7b2102",
    "title": "Operating Systems Overview",
    "input_text": "This audiobook covers process management, CPU scheduling, memory management, and file systems in modern operating systems.",
    "input_method": "text",
    "file_name": null,
    "audio_url": null,
    "duration": null,
    "status": "processing",
    "error_message": null,
    "created_at": "2025-12-21T11:40:00.000Z",
    "updated_at": "2025-12-21T11:40:00.000Z"
  },
  {
    "id": "a7b4c1d9-8a2e-4e9f-b10e-3c5d2f9a3303",
    "title": "Neural Networks Basics",
    "input_text": "Neural networks are computational models inspired by the human brain and are widely used in pattern recognition and machine learning.",
    "input_method": "text",
    "file_name": null,
    "audio_url": null,
    "duration": null,
    "status": "failed",
    "error_message": "Text length exceeds the maximum allowed limit.",
    "created_at": "2025-12-20T18:25:00.000Z",
    "updated_at": "2025-12-20T18:25:00.000Z"
  },
  {
    "id": "f5e2d8c4-6b19-4e5a-9b73-2c6f91e44204",
    "title": "Database Indexing Explained",
    "input_text": "This audiobook explains how database indexes work, their internal data structures, and how they improve query performance.",
    "input_method": "file",
    "file_name": "database_indexing_notes.pdf",
    "audio_url": "https://your-supabase-bucket.supabase.co/storage/v1/object/public/audiobooks/database_indexing_notes.mp3",
    "duration": 512,
    "status": "completed",
    "error_message": null,
    "created_at": "2025-12-19T14:10:00.000Z",
    "updated_at": "2025-12-19T14:10:00.000Z"
  }
]


export function AudiobookLibrary() {
  const [generations, setGenerations] = useState<AudiobookGeneration[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadGenerations();

    const channel = supabase
      .channel('audiobook_changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'audiobook_generations' },
        () => {
          loadGenerations();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const loadGenerations = async () => {
    try {
      const { data, error } = await supabase
        .from('audiobook_generations')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(20);

      if (error) throw error;
      setGenerations(data || []);
    } catch (error) {
      console.error('Error loading generations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getStatusBadge = (status: AudiobookGeneration['status']) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      processing: 'bg-blue-100 text-blue-700 border-blue-200',
      completed: 'bg-green-100 text-green-700 border-green-200',
      failed: 'bg-red-100 text-red-700 border-red-200',
    };

    const icons = {
      pending: Clock,
      processing: Loader2,
      completed: Play,
      failed: AlertCircle,
    };

    const Icon = icons[status];

    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${styles[status]}`}>
        <Icon className={`w-3.5 h-3.5 ${status === 'processing' ? 'animate-spin' : ''}`} />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="flex items-center gap-3 mb-8">
        <Library className="w-8 h-8 text-blue-600" />
        <h2 className="text-3xl font-bold text-gray-900">Your Audiobook Library</h2>
      </div>

      {generations.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center">
          <Library className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No audiobooks yet</h3>
          <p className="text-gray-500">
            Create your first audiobook using the form on the main page.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {generations.map((generation) => (
            <div
              key={generation.id}
              className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-lg transition-all"
            >
              <div className="flex flex-col gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <h3 className="text-xl font-semibold text-gray-900">{generation.title}</h3>
                    {getStatusBadge(generation.status)}
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-4">
                    <div className="flex items-center gap-1.5">
                      {generation.input_method === 'file' ? (
                        <>
                          <FileText className="w-4 h-4" />
                          <span>File: {generation.file_name || 'Unknown'}</span>
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4" />
                          <span>Text input</span>
                        </>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-4 h-4" />
                      <span>{formatDate(generation.created_at)}</span>
                    </div>
                    {generation.duration && (
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-4 h-4" />
                        <span>{Math.floor(generation.duration / 60)}m {generation.duration % 60}s</span>
                      </div>
                    )}
                  </div>

                  <p className="text-gray-600 text-sm line-clamp-2">
                    {generation.input_text.substring(0, 200)}
                    {generation.input_text.length > 200 ? '...' : ''}
                  </p>

                  {generation.error_message && (
                    <div className="mt-3 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                      {generation.error_message}
                    </div>
                  )}
                </div>

                {generation.status === 'completed' && generation.audio_url && (
                  <div className="flex-shrink-0">
                    <audio controls className="w-64">
                      <source src={generation.audio_url} type="audio/mpeg" />
                    </audio>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
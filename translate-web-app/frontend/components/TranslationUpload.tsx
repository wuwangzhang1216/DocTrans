"use client"

import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Download, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { addToHistory } from '@/components/TranslationHistory';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';
const WS_URL = API_URL.replace('http', 'ws');

interface TranslationJob {
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  outputFile?: string;
  error?: string;
  message?: string;
}

const SUPPORTED_FORMATS = ['.pdf', '.docx', '.pptx', '.txt', '.md'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export default function TranslationUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [targetLanguage, setTargetLanguage] = useState('Chinese');
  const [job, setJob] = useState<TranslationJob | null>(null);
  const [uploading, setUploading] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // WebSocket connection for job updates
  useEffect(() => {
    if (!job?.jobId) return;

    let websocket: WebSocket | null = null;
    let pollInterval: NodeJS.Timeout | null = null;

    // Try to connect via WebSocket for real-time updates
    try {
      websocket = new WebSocket(`${WS_URL}/ws/${job.jobId}`);

      websocket.onopen = () => {
        console.log('WebSocket connected');
      };

      websocket.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);

          setJob(current => {
            if (!current || current.jobId !== update.jobId) return current;
            const updatedJob = {
              ...current,
              ...update
            } as TranslationJob;

            return updatedJob;
          });
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error, falling back to polling');
      };

      websocket.onclose = () => {
        console.log('WebSocket disconnected');
      };

      setWs(websocket);
    } catch (error) {
      console.error('Failed to create WebSocket, using polling only');
    }

    // Fallback polling mechanism
    pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/job/${job.jobId}`);
        if (response.ok) {
          const data = await response.json();

          setJob(current => {
            const updatedJob = {
              ...current,
              jobId: job.jobId,
              status: data.status,
              progress: data.progress || 0,
              message: data.message || '',
              outputFile: data.outputFile,
              error: data.error
            };
            return updatedJob;
          });

          // Stop polling if job is completed or failed
          if (data.status === 'completed' || data.status === 'failed') {
            if (pollInterval) clearInterval(pollInterval);
          }
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => {
      if (websocket) websocket.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [job?.jobId]);

  // Handle history update when job completes (separate effect to avoid render-phase updates)
  useEffect(() => {
    if (job?.status === 'completed' && job.outputFile && file) {
      addToHistory({
        jobId: job.jobId,
        fileName: file.name,
        targetLanguage,
        completedAt: Date.now(),
        outputFile: job.outputFile
      });
    }
  }, [job?.status, job?.outputFile, job?.jobId, file, targetLanguage]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];

      // Validate file type
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!SUPPORTED_FORMATS.includes(ext)) {
        alert(`File type ${ext} is not supported. Supported formats: ${SUPPORTED_FORMATS.join(', ')}`);
        return;
      }

      // Validate file size
      if (file.size > MAX_FILE_SIZE) {
        alert('File size exceeds 10MB limit');
        return;
      }

      setFile(file);
      setJob(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md']
    },
    maxFiles: 1,
    multiple: false
  });

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('targetLanguage', targetLanguage);

    try {
      const response = await fetch(`${API_URL}/api/translate`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setJob({
          jobId: data.jobId,
          status: 'queued',
          progress: 0,
          message: 'Job queued for processing'
        });
      } else {
        throw new Error(data.error || 'Upload failed');
      }
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = () => {
    if (job?.outputFile) {
      window.open(`${API_URL}/api/download/${job.outputFile}`, '_blank');
    }
  };

  const handleReset = () => {
    setFile(null);
    setJob(null);
  };

  const getStatusIcon = () => {
    if (!job) return null;

    switch (job.status) {
      case 'queued':
        return <Loader2 className="h-5 w-5 animate-spin text-[#fbbf24]" />;
      case 'processing':
        return <Loader2 className="h-5 w-5 animate-spin text-[#f97316]" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    if (!job) return 'bg-gray-200';

    switch (job.status) {
      case 'queued':
        return 'bg-blue-500';
      case 'processing':
        return 'bg-yellow-500';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-gray-200';
    }
  };

  return (
    <Card className="w-full max-w-3xl mx-auto bg-white/5 backdrop-blur-md border border-white/10 shadow-xl">
      <CardContent className="pt-8 space-y-6">
        {/* Language Selection */}
        <div className="space-y-3">
          <Label htmlFor="language-select" className="text-sm font-medium text-white">Target Language</Label>
          <Select
            value={targetLanguage}
            onValueChange={setTargetLanguage}
            disabled={uploading || (!!job && job.status === 'processing')}
          >
            <SelectTrigger id="language-select" className="w-full h-11">
              <SelectValue placeholder="Select a language" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="English">English</SelectItem>
              <SelectItem value="Chinese">中文</SelectItem>
              <SelectItem value="Spanish">Español</SelectItem>
              <SelectItem value="French">Français</SelectItem>
              <SelectItem value="German">Deutsch</SelectItem>
              <SelectItem value="Japanese">日本語</SelectItem>
              <SelectItem value="Korean">한국어</SelectItem>
              <SelectItem value="Portuguese">Português</SelectItem>
              <SelectItem value="Russian">Русский</SelectItem>
              <SelectItem value="Arabic">العربية</SelectItem>
              <SelectItem value="Hindi">हिन्दी</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* File Upload Area */}
        {!file && !job && (
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200
              ${isDragActive ? 'border-[#f97316] bg-gradient-to-br from-[#fbbf24]/5 to-[#f97316]/5 scale-[0.98]' : 'border-white/20 hover:border-[#f97316]/50 hover:bg-white/5'}`}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center space-y-4">
              <div className={`p-4 rounded-full transition-all ${isDragActive ? 'bg-gradient-to-br from-[#fbbf24]/20 to-[#f97316]/20' : 'bg-white/5'}`}>
                <Upload className={`h-8 w-8 transition-colors ${isDragActive ? 'text-[#f97316]' : 'text-gray-400'}`} />
              </div>
              {isDragActive ? (
                <p className="text-base font-medium text-white">Drop your file here</p>
              ) : (
                <>
                  <div className="space-y-2">
                    <p className="text-base font-medium text-white">Drop your file here or click to browse</p>
                    <p className="text-sm text-gray-400">
                      {SUPPORTED_FORMATS.join(', ')} · Max 10MB
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Selected File Display */}
        {file && !job && (
          <div className="border border-white/10 rounded-xl p-5 bg-white/5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="p-3 rounded-lg bg-gradient-to-br from-[#fbbf24]/20 to-[#f97316]/20">
                  <FileText className="h-6 w-6 text-[#f97316]" />
                </div>
                <div>
                  <p className="font-medium text-sm text-white">{file.name}</p>
                  <p className="text-sm text-gray-400 mt-0.5">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
                className="text-gray-400 hover:text-white"
              >
                Remove
              </Button>
            </div>
          </div>
        )}

        {/* Job Status */}
        {job && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {getStatusIcon()}
                <div>
                  <Badge variant={job.status === 'completed' ? 'default' : job.status === 'failed' ? 'destructive' : 'secondary'} className="capitalize">
                    {job.status}
                  </Badge>
                </div>
              </div>
              <span className="text-sm font-medium tabular-nums">{job.progress}%</span>
            </div>

            <Progress value={job.progress} className="h-2" />

            {job.message && (
              <p className="text-sm text-gray-400">{job.message}</p>
            )}

            {job.error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{job.error}</AlertDescription>
              </Alert>
            )}

            {job.status === 'completed' && job.outputFile && (
              <div className="space-y-3 pt-2">
                <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-4">
                  <div className="flex items-start space-x-3">
                    <CheckCircle className="h-5 w-5 text-green-400 mt-0.5" />
                    <div className="flex-1 space-y-1">
                      <p className="text-sm font-medium text-green-300">Translation completed</p>
                      <p className="text-sm text-green-400/80">Your document is ready for download</p>
                    </div>
                  </div>
                </div>
                <Button onClick={handleDownload} className="w-full h-11 bg-gradient-to-r from-[#fbbf24] to-[#f97316] hover:from-[#f59e0b] hover:to-[#ea580c] text-white" size="lg">
                  <Download className="mr-2 h-4 w-4" />
                  Download Translated Document
                </Button>
              </div>
            )}

            {(job.status === 'completed' || job.status === 'failed') && (
              <Button
                variant="ghost"
                onClick={handleReset}
                className="w-full h-11 border border-white/20 text-white hover:bg-white/10 bg-transparent"
              >
                Translate Another Document
              </Button>
            )}
          </div>
        )}
      </CardContent>

      {/* Upload Button */}
      {file && !job && (
        <CardFooter className="px-8 pb-8 pt-0">
          <Button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full h-11 bg-gradient-to-r from-[#fbbf24] to-[#f97316] hover:from-[#f59e0b] hover:to-[#ea580c] text-white border-0"
            size="lg"
          >
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Start Translation
              </>
            )}
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}
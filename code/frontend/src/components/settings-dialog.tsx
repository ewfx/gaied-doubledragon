import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import { ProcessingDialog } from './processing-dialog';
import { emailApi } from '../services/api';

interface SettingsDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ConfigFile {
  name: string;
  size: number;
}

export function SettingsDialog({ isOpen, onOpenChange }: SettingsDialogProps) {
  const [configFile, setConfigFile] = useState<ConfigFile | null>(null);
  const [prompt, setPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  
const onDrop = useCallback((acceptedFiles: File[]) => {
  if (acceptedFiles.length > 0) {
    setConfigFile(acceptedFiles[0]);
  }
}, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/json': ['.json']
    },
    maxFiles: 1
  });

  const removeFile = () => {
    setConfigFile(null);
  };

  const handleConfigure = async () => {
    if (configFile) {
      try {
        setIsProcessing(true);
        onOpenChange(false);
        await emailApi.configureModel(configFile, prompt);
        // Reset state after successful configuration
        setConfigFile(null);
        setPrompt('');
      } catch (error) {
        console.error('Failed to configure model:', error);
        // Handle error appropriately
      } finally {
        setIsProcessing(false);
      }
    }
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onOpenChange}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-xl">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-zinc-100">
              Model Configuration
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Config File Upload */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-200">
                Configuration File
              </label>
              <div
                {...getRootProps()}
                className={`mt-1 p-6 border-2 border-dashed rounded-xl transition-colors ${
                  isDragActive 
                    ? 'border-brand-500 bg-brand-500/10' 
                    : 'border-zinc-700 hover:border-brand-500'
                }`}
              >
                <input {...getInputProps()} />
                {!configFile ? (
                  <div className="flex flex-col items-center justify-center text-sm text-zinc-400">
                    <Upload className="w-8 h-8 mb-4 text-zinc-500" />
                    <p className="font-medium">
                      {isDragActive
                        ? "Drop the configuration file here"
                        : "Drag 'n' drop a JSON file, or click to select"}
                    </p>
                    <p className="mt-1">Supports .json files</p>
                  </div>
                ) : (
                  <div className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Upload className="w-4 h-4 text-zinc-400" />
                      <span className="text-sm text-zinc-300 truncate max-w-[300px]">
                        {configFile.name}
                      </span>
                      <span className="text-xs text-zinc-500">
                        ({(configFile.size / 1024).toFixed(1)} KB)
                      </span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFile();
                      }}
                      className="p-1 hover:bg-zinc-700 rounded-full transition-colors"
                    >
                      <X className="w-4 h-4 text-zinc-400" />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Prompt Input */}
            <div className="space-y-2">
              <label 
                htmlFor="prompt" 
                className="text-sm font-medium text-zinc-200"
              >
                Model Prompt
              </label>
              <textarea
                id="prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter your model prompt here..."
                className="w-full h-32 px-4 py-3 bg-zinc-800/50 border border-zinc-700 rounded-xl text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              />
            </div>
          </div>

          <DialogFooter>
            <button
              onClick={handleConfigure}
              disabled={!configFile || !prompt}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-brand-500 rounded-lg hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 focus:ring-offset-zinc-900 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Configure
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ProcessingDialog 
        isOpen={isProcessing}
        onOpenChange={setIsProcessing}
      />
    </>
  );
}

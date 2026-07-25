import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Link as LinkIcon, Image as ImageIcon, UploadCloud, X, Lock } from 'lucide-react';
import clsx from 'clsx';

export default function CommandCenter({ onAnalyze, isLoading }) {
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [image, setImage] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const textareaRef = useRef(null);

  // Auto-expand textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.max(120, textareaRef.current.scrollHeight)}px`;
    }
  }, [text]);

  const isValidUrl = (string) => {
    try {
      const url = new URL(string);
      return url.protocol === 'https:';
    } catch (_) {
      return false;
    }
  };

  const hasValidInput = text.trim().length > 10 || isValidUrl(url) || image;

  const handleSubmit = () => {
    if (!hasValidInput || isLoading) return;

    let payload = {};
    if (image) {
      payload = { input_type: 'image', image_base64: image };
    } else if (isValidUrl(url)) {
      payload = { input_type: 'url', input_text: url };
    } else {
      payload = { input_type: 'text', input_text: text };
    }
    
    onAnalyze(payload);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageFile(e.dataTransfer.files[0]);
    }
  };
  
  const handleImageFile = (file) => {
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (e) => setImage(e.target.result);
    reader.readAsDataURL(file);
    // Clear other inputs when image is added
    setText('');
    setUrl('');
  };

  const clearImage = () => setImage(null);

  return (
    <div className="w-full relative">
      {/* Loading Skeleton Overlay */}
      <AnimatePresence>
        {isLoading && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-10 bg-surface-900/50 backdrop-blur-sm rounded-2xl flex items-center justify-center"
          >
            <div className="flex flex-col items-center gap-4">
              <div className="w-16 h-16 relative">
                <div className="absolute inset-0 border-4 border-primary/20 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-primary rounded-full border-t-transparent animate-spin"></div>
              </div>
              <span className="text-primary font-medium tracking-widest uppercase text-sm animate-pulse">Running Multi-Vector Analysis...</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className={clsx("glass-card p-6 md:p-8 flex flex-col gap-8", isLoading && "opacity-50 pointer-events-none")}>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Left: Text Input */}
          <div className="flex flex-col gap-3">
            <label className="text-sm font-semibold text-text flex items-center gap-2">
              <Search className="w-4 h-4 text-primary" />
              Claim or Text Segment
            </label>
            <textarea
              ref={textareaRef}
              value={text}
              onChange={(e) => { setText(e.target.value); if(e.target.value) { setUrl(''); clearImage(); } }}
              placeholder="Paste a suspicious claim, news excerpt, or social media post for context analysis..."
              className="w-full bg-surface-800 border border-white/5 rounded-xl p-4 text-text placeholder-text-muted focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all resize-none min-h-[120px]"
            />
          </div>

          {/* Right: URL & Image Upload */}
          <div className="flex flex-col gap-6">
            
            {/* URL Input */}
            <div className="flex flex-col gap-3">
              <label className="text-sm font-semibold text-text flex items-center gap-2">
                <LinkIcon className="w-4 h-4 text-primary" />
                Article URL
                <span className="ml-auto flex items-center gap-1 text-[10px] uppercase tracking-wider bg-success/20 text-success px-2 py-0.5 rounded-full border border-success/30">
                  <Lock className="w-3 h-3" />
                  HTTPS Only
                </span>
              </label>
              <div className="relative">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => { setUrl(e.target.value); if(e.target.value) { setText(''); clearImage(); } }}
                  placeholder="https://example.com/news-article"
                  className="w-full bg-surface-800 border border-white/5 rounded-xl pl-10 pr-4 py-3.5 text-text placeholder-text-muted focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
                />
                <LinkIcon className="w-5 h-5 text-text-muted absolute left-3.5 top-3.5" />
              </div>
            </div>

            {/* Image Dropzone */}
            <div className="flex flex-col gap-3 h-full">
               <label className="text-sm font-semibold text-text flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-primary" />
                VisualLens (Image Analysis)
              </label>
              
              <div 
                className={clsx(
                  "flex-1 relative rounded-xl border-2 border-dashed transition-all duration-200 flex flex-col items-center justify-center p-6 text-center min-h-[120px]",
                  dragActive ? "border-primary bg-primary/5" : "border-white/10 bg-surface-800 hover:border-white/20 hover:bg-surface-700/50",
                  image ? "border-none p-1 bg-surface-900" : ""
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                {image ? (
                  <div className="relative w-full h-full min-h-[140px] rounded-lg overflow-hidden group">
                    <img src={image} alt="Upload preview" className="w-full h-full object-cover rounded-lg" />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <button onClick={(e) => { e.stopPropagation(); clearImage(); }} className="bg-alert text-white p-2 rounded-full hover:scale-110 transition-transform shadow-lg">
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <input 
                      type="file" 
                      accept="image/*"
                      onChange={(e) => e.target.files?.[0] && handleImageFile(e.target.files[0])}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <UploadCloud className={clsx("w-8 h-8 mb-3 transition-colors", dragActive ? "text-primary" : "text-text-muted")} />
                    <p className="text-sm text-text-muted">
                      <span className="text-primary font-medium">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-xs text-text-muted/70 mt-1">PNG, JPG up to 10MB</p>
                  </>
                )}
              </div>
            </div>

          </div>
        </div>

        {/* Center CTA */}
        <div className="flex justify-center mt-2">
          <button
            onClick={handleSubmit}
            disabled={!hasValidInput || isLoading}
            className="btn-primary px-8 py-3.5 text-lg flex items-center gap-2 group w-full md:w-auto min-w-[240px] justify-center"
          >
            <Search className="w-5 h-5 group-hover:animate-pulse" />
            {isLoading ? 'Analyzing...' : 'Analyze Context'}
          </button>
        </div>

      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Image as ImageIcon, UploadCloud, X, Youtube, Loader2, AlertCircle, ShieldCheck } from 'lucide-react';
import api from '../services/api';

export default function VisualLens() {
  const [image, setImage] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [userQuery, setUserQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => setImage(e.target.result);
        reader.readAsDataURL(file);
        setYoutubeUrl('');
        setResult(null);
        setError(null);
      }
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = (e) => setImage(e.target.result);
      reader.readAsDataURL(file);
      setYoutubeUrl('');
      setResult(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!image && !youtubeUrl) return;
    setIsLoading(true);
    setResult(null);
    setError(null);

    try {
      if (image) {
        // Strip data:image/png;base64, prefix if needed by backend, though backend usually handles it
        const b64 = image.split(',')[1] || image;
        const res = await api.analyzeImage({ image_base64: b64, user_query: userQuery });
        setResult(res);
      } else if (youtubeUrl) {
        const res = await api.analyze({ input_text: youtubeUrl, input_type: 'youtube', user_query: userQuery });
        setResult(res);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-8 w-full max-w-4xl mx-auto"
    >
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-display font-bold text-slate-900 dark:text-slate-50">VisualLens</h2>
        <p className="text-slate-500 dark:text-slate-400">Perform forensic analysis on images and extract context from YouTube videos.</p>
      </div>

      <div className="glass-card p-6 md:p-8 flex flex-col gap-8">
        
        {/* Image Dropzone */}
        <div className="flex flex-col gap-3">
          <label className="text-sm font-semibold flex items-center gap-2 text-textMain-light dark:text-textMain-dark">
            <ImageIcon className="w-4 h-4 text-primary" />
            Image Upload
          </label>
          <div 
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className={`relative rounded-xl border-2 border-dashed ${image ? 'border-none p-0' : 'border-borderBase-light dark:border-borderBase-dark hover:border-primary hover:bg-primary/5'} bg-surface-light dark:bg-surface-dark transition-all duration-200 flex flex-col items-center justify-center p-8 min-h-[200px] overflow-hidden group`}
          >
            {image ? (
              <>
                <img src={image} alt="Upload" className="w-full h-full object-cover rounded-lg max-h-[400px]" />
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <button onClick={() => setImage(null)} className="bg-alert text-white p-3 rounded-full hover:scale-110 transition-transform shadow-lg">
                    <X className="w-6 h-6" />
                  </button>
                </div>
              </>
            ) : (
              <>
                <input type="file" accept="image/*" onChange={handleFileInput} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                <UploadCloud className="w-10 h-10 mb-4 text-textMuted-light dark:text-textMuted-dark" />
                <p className="text-sm text-textMuted-light dark:text-textMuted-dark text-center">
                  <span className="text-primary font-medium">Click to upload</span> or drag and drop<br/>
                  <span className="text-xs opacity-70 mt-1 block">PNG, JPG up to 10MB</span>
                </p>
              </>
            )}
          </div>
        </div>

        {/* OR Divider */}
        <div className="flex items-center gap-4">
          <div className="flex-1 h-px bg-borderBase-light dark:bg-borderBase-dark"></div>
          <span className="text-xs font-medium text-textMuted-light dark:text-textMuted-dark uppercase tracking-widest">OR</span>
          <div className="flex-1 h-px bg-borderBase-light dark:bg-borderBase-dark"></div>
        </div>

        {/* YouTube Input */}
        <div className="flex flex-col gap-3">
          <label className="text-sm font-semibold flex items-center gap-2 text-textMain-light dark:text-textMain-dark">
            <Youtube className="w-4 h-4 text-alert" />
            YouTube Video URL
          </label>
          <div className="relative">
            <input 
              type="url" 
              value={youtubeUrl}
              onChange={(e) => { setYoutubeUrl(e.target.value); setImage(null); }}
              placeholder="https://youtube.com/watch?v=..." 
              className="w-full bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark rounded-xl pl-10 pr-4 py-3.5 text-textMain-light dark:text-textMain-dark placeholder-textMuted-light/50 dark:placeholder-textMuted-dark/50 focus:outline-none focus:border-alert/50 focus:ring-1 focus:ring-alert/50 transition-all" 
            />
            <Youtube className="w-5 h-5 text-textMuted-light dark:text-textMuted-dark absolute left-3.5 top-3.5" />
          </div>
        </div>

        {/* User Query Input */}
        <div className="flex flex-col gap-3 pt-4 border-t border-borderBase-light dark:border-borderBase-dark">
          <label className="text-sm font-semibold flex items-center gap-2 text-textMain-light dark:text-textMain-dark">
            <span className="text-primary font-bold">?</span> Context / Query (Optional)
          </label>
          <div className="relative">
            <textarea 
              value={userQuery}
              onChange={(e) => setUserQuery(e.target.value)}
              placeholder="E.g., Did the speaker actually claim that the economy crashed in this video?" 
              className="w-full bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark rounded-xl px-4 py-3 text-textMain-light dark:text-textMain-dark placeholder-textMuted-light/50 dark:placeholder-textMuted-dark/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all resize-none min-h-[80px]"
            />
          </div>
        </div>

        {error && (
          <div className="bg-alert/10 border border-alert/20 text-alert p-4 rounded-xl flex items-center gap-3">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        <button 
          onClick={handleAnalyze}
          disabled={(!image && !youtubeUrl) || isLoading}
          className="btn-primary py-4 mt-2 text-lg font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isLoading ? <><Loader2 className="w-5 h-5 animate-spin" /> Analyzing...</> : <><ImageIcon className="w-5 h-5" /> Run Visual Analysis</>}
        </button>

        <AnimatePresence>
          {result && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="border-t border-borderBase-light dark:border-borderBase-dark pt-8 mt-4 flex flex-col gap-4"
            >
              <h3 className="text-2xl font-display font-bold text-slate-900 dark:text-white">Analysis Result</h3>
              <div className="glass-card p-6 border-l-4 border-l-primary flex flex-col gap-4">
                {result.label ? (
                  <>
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-6 h-6 text-primary" />
                      <span className="text-lg font-semibold capitalize text-slate-800 dark:text-slate-100">{result.label.replace('_', ' ')}</span>
                      <span className="ml-auto text-sm bg-surface-light dark:bg-surface-dark px-3 py-1 rounded-full border border-borderBase-light dark:border-borderBase-dark font-mono">
                        {Math.round(result.confidence * 100)}% Match
                      </span>
                    </div>
                    {result.metadata && (
                      <div className="text-sm text-textMuted-light dark:text-textMuted-dark grid grid-cols-2 gap-2 mt-2">
                        <div>Format: {result.metadata.format}</div>
                        <div>Size: {result.metadata.size}</div>
                        <div>Mode: {result.metadata.mode}</div>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <p className="text-sm text-textMuted-light dark:text-textMuted-dark leading-relaxed">
                      {result.answer || "YouTube analysis complete."}
                    </p>
                    {result.context_summary && (
                      <p className="text-sm text-primary font-medium mt-2 bg-primary/10 p-3 rounded-lg border border-primary/20">
                        {result.context_summary}
                      </p>
                    )}
                  </>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>


      </div>
    </motion.div>
  );
}

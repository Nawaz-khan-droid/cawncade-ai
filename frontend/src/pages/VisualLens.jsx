import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Image as ImageIcon, UploadCloud, X, Youtube, ShieldCheck, Eye, Database, FileText } from 'lucide-react';
import api from '../services/api';

// Shared UI Primitives
import ResultHero from '../components/ui/ResultHero';
import SourceCard from '../components/ui/SourceCard';
import LoadingState from '../components/ui/LoadingState';
import EmptyState from '../components/ui/EmptyState';
import ErrorState from '../components/ui/ErrorState';

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
      className="flex flex-col gap-5 w-full max-w-4xl mx-auto px-2 md:px-0"
    >
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl md:text-3xl font-display font-bold text-slate-900 dark:text-slate-50">VisualLens</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">Perform forensic analysis on images and extract context from YouTube videos.</p>
      </div>

      <div className="glass-card p-4 md:p-6 flex flex-col gap-5">
        
        {/* Image Dropzone */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold uppercase tracking-wider flex items-center gap-2 text-textMain-light dark:text-textMain-dark">
            <ImageIcon className="w-3.5 h-3.5 text-primary" />
            Image Upload
          </label>
          <div 
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className={`relative rounded-xl border-2 border-dashed ${image ? 'border-none p-0' : 'border-borderBase-light dark:border-borderBase-dark hover:border-primary hover:bg-primary/5'} bg-surface-light dark:bg-surface-dark transition-all duration-200 flex flex-col items-center justify-center p-6 min-h-[160px] overflow-hidden group`}
          >
            {image ? (
              <>
                <img src={image} alt="Upload" className="w-full h-full object-cover rounded-lg max-h-[350px]" />
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <button onClick={() => setImage(null)} className="bg-alert text-white p-3 rounded-full hover:scale-110 transition-transform shadow-lg">
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </>
            ) : (
              <>
                <input type="file" accept="image/*" onChange={handleFileInput} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                <UploadCloud className="w-8 h-8 mb-2 text-textMuted-light dark:text-textMuted-dark" />
                <p className="text-xs text-textMuted-light dark:text-textMuted-dark text-center">
                  <span className="text-primary font-bold">Click to upload</span> or drag and drop<br/>
                  <span className="text-[10px] opacity-70 mt-0.5 block">PNG, JPG up to 10MB</span>
                </p>
              </>
            )}
          </div>
        </div>

        {/* OR Divider */}
        <div className="flex items-center gap-4">
          <div className="flex-1 h-px bg-borderBase-light dark:bg-borderBase-dark"></div>
          <span className="text-[10px] font-bold text-textMuted-light dark:text-textMuted-dark uppercase tracking-widest">OR</span>
          <div className="flex-1 h-px bg-borderBase-light dark:bg-borderBase-dark"></div>
        </div>

        {/* YouTube Input */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold uppercase tracking-wider flex items-center gap-2 text-textMain-light dark:text-textMain-dark">
            <Youtube className="w-3.5 h-3.5 text-alert" />
            YouTube Video URL
          </label>
          <div className="relative">
            <input 
              type="url" 
              value={youtubeUrl}
              onChange={(e) => { setYoutubeUrl(e.target.value); setImage(null); }}
              placeholder="https://youtube.com/watch?v=..." 
              className="w-full bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark rounded-xl pl-10 pr-4 py-2.5 text-sm text-textMain-light dark:text-textMain-dark placeholder-textMuted-light/50 dark:placeholder-textMuted-dark/50 focus:outline-none focus:border-alert/50 focus:ring-1 focus:ring-alert/50 transition-all" 
            />
            <Youtube className="w-4 h-4 text-textMuted-light dark:text-textMuted-dark absolute left-3.5 top-3" />
          </div>
        </div>

        {/* User Query Input */}
        <div className="flex flex-col gap-2 pt-3 border-t border-borderBase-light dark:border-borderBase-dark">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold uppercase tracking-wider flex items-center gap-2 text-textMain-light dark:text-textMain-dark">
              <span className="text-primary font-bold">?</span> Context / Query (Optional)
            </label>
            <span className="text-[11px] font-mono text-slate-400">
              {userQuery.length.toLocaleString()} / 5,000
            </span>
          </div>
          <textarea 
            value={userQuery}
            onChange={(e) => setUserQuery(e.target.value)}
            maxLength={5000}
            placeholder="E.g., Did the speaker actually claim that the economy crashed in this video?" 
            className="w-full bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark rounded-xl px-3.5 py-2.5 text-sm text-textMain-light dark:text-textMain-dark placeholder-textMuted-light/50 dark:placeholder-textMuted-dark/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all resize-none min-h-[70px]"
          />
        </div>

        {error && <ErrorState error={error} onRetry={handleAnalyze} />}

        <button 
          onClick={handleAnalyze}
          disabled={(!image && !youtubeUrl) || isLoading}
          className="btn-primary py-3 text-base font-semibold flex items-center justify-center gap-2 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          {isLoading ? 'Running Visual Forensics...' : 'Run Visual Analysis'}
        </button>

        {/* LOADING STATE */}
        {isLoading && <LoadingState message="Extracting Video Keyframes & Running ELA/EXIF Forensics..." />}

        {/* RESULT SECTION - 5-CARD FORENSICS ARCHITECTURE */}
        <AnimatePresence>
          {result && !isLoading && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="border-t border-borderBase-light dark:border-borderBase-dark pt-5 flex flex-col gap-4"
            >
              {/* 1. REUSABLE HERO VERDICT CARD */}
              <ResultHero result={result} />

              {/* 2. FORENSIC NARRATIVE SUMMARY */}
              <div className="glass-card p-4 md:p-6 flex flex-col gap-2 rounded-2xl">
                <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                  <FileText className="w-4 h-4 text-primary" />
                  <span className="text-xs font-extrabold uppercase tracking-widest text-slate-400">Forensic Analysis Summary</span>
                </div>
                <p className="text-sm font-medium text-slate-200 leading-relaxed">
                  {result.answer || result.context_summary || "Visual analysis complete."}
                </p>
              </div>

              {/* 3. FORENSIC INDICATORS & METADATA */}
              <div className="glass-card p-4 md:p-6 flex flex-col gap-3 rounded-2xl">
                <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                  <Eye className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-extrabold uppercase tracking-widest text-slate-400">Forensic Indicators & Metadata</span>
                </div>

                {image ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 text-xs">
                    <div className="p-3 rounded-xl bg-white/5 border border-white/5 flex flex-col gap-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400">Match Score</span>
                      <span className="text-base font-bold text-emerald-400">{Math.round((result.confidence || 0) * 100)}%</span>
                    </div>
                    <div className="p-3 rounded-xl bg-white/5 border border-white/5 flex flex-col gap-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400">Format</span>
                      <span className="text-sm font-semibold text-slate-200">{result.metadata?.format || 'PNG / JPG'}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-white/5 border border-white/5 flex flex-col gap-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400">Dimensions</span>
                      <span className="text-sm font-semibold text-slate-200">{result.metadata?.size || 'Auto-Detected'}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-white/5 border border-white/5 flex flex-col gap-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400">Analysis Mode</span>
                      <span className="text-sm font-semibold text-slate-200">{result.metadata?.mode || 'RGB'}</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 text-xs text-slate-400 italic">
                    ℹ️ No image file was uploaded for this analysis. Forensic metadata analysis is omitted for text and video-only inputs.
                  </div>
                )}
              </div>

              {/* 4. SOURCES & EVIDENCE MATCHES */}
              {result.sources_cited && result.sources_cited.length > 0 ? (
                <div className="flex flex-col gap-2.5">
                  <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-400">
                    Retrieved Visual References ({result.sources_cited.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {result.sources_cited.map((src, idx) => (
                      <SourceCard key={idx} src={src} />
                    ))}
                  </div>
                </div>
              ) : (
                <EmptyState title="No Visual Duplicates Found" description="No direct reverse-image matches were detected in public index databases." />
              )}
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </motion.div>
  );
}

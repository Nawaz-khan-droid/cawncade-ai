import React, { useState, useRef } from 'react';
import { Search, Link, FileText, Youtube, Image as ImageIcon, Upload, Loader2, X } from 'lucide-react';
import api from '../services/api';

export default function InputBox({ onSubmit, isLoading }) {
  const [input, setInput] = useState('');
  const [inputType, setInputType] = useState('text');
  const [previewImage, setPreviewImage] = useState(null);
  const [imageBase64, setImageBase64] = useState(null);
  const fileInputRef = useRef(null);

  const detectType = (value) => {
    if (value.match(/youtube\.com|youtu\.be/i)) setInputType('youtube');
    else if (value.match(/^https?:\/\//i)) setInputType('url');
    else setInputType('text');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isLoading) return;
    if (inputType === 'image') {
      if (imageBase64) onSubmit({ image_base64: imageBase64, input_type: 'image' });
    } else {
      if (input.trim()) onSubmit({ input_text: input.trim(), input_type: inputType, max_sources: 10 });
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) { alert('Image must be under 10MB'); return; }
    setPreviewImage(URL.createObjectURL(file));
    const base64 = await api.fileToBase64(file);
    setImageBase64(base64.split(',')[1]);
  };

  const clearImage = () => {
    setPreviewImage(null);
    setImageBase64(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const typeButtons = [
    { id: 'text', icon: FileText, label: 'Text/Claim' },
    { id: 'url', icon: Link, label: 'URL' },
    { id: 'youtube', icon: Youtube, label: 'YouTube' },
    { id: 'image', icon: ImageIcon, label: 'Visual Lens' },
  ];

  const placeholders = { text: 'Enter a claim, headline, or topic to verify...', url: 'Paste a news URL to verify...', youtube: 'Paste a YouTube video URL...', image: 'Upload an image for deepfake/AI detection...' };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-4">
      <div className="flex items-center justify-center gap-1">
        {typeButtons.map(({ id, icon: Icon, label }) => (
          <button key={id} type="button" onClick={() => setInputType(id)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-all text-sm font-medium ${inputType === id ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30' : 'text-gray-500 hover:text-gray-300 border border-transparent hover:border-white/10'}`}
            title={label}>
            <Icon className="w-4 h-4" />
            <span className="hidden sm:inline">{label}</span>
          </button>
        ))}
      </div>
      <form onSubmit={handleSubmit}>
        <div className="glass-card p-2 flex items-center gap-2">
          <div className="pl-2 text-gray-500">
            {inputType === 'image' ? <ImageIcon className="w-5 h-5" /> : <Search className="w-5 h-5" />}
          </div>
          {inputType === 'image' ? (
            <div className="flex-1 flex items-center gap-3">
              {previewImage ? (
                <div className="relative flex items-center gap-3 flex-1">
                  <img src={previewImage} alt="Preview" className="h-12 w-12 object-cover rounded-lg" />
                  <span className="text-sm text-gray-300 truncate">Image ready for analysis</span>
                  <button type="button" onClick={clearImage} className="text-gray-500 hover:text-red-400"><X className="w-4 h-4" /></button>
                </div>
              ) : (
                <label className="flex-1 flex items-center gap-3 px-3 py-3 cursor-pointer hover:bg-white/5 rounded-lg transition-colors">
                  <Upload className="w-5 h-5 text-gray-500" />
                  <span className="text-gray-400 text-sm">Click to upload an image (JPG, PNG, WebP)</span>
                  <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleImageUpload} className="hidden" />
                </label>
              )}
            </div>
          ) : (
            <input type="text" value={input} onChange={(e) => { setInput(e.target.value); detectType(e.target.value); }}
              placeholder={placeholders[inputType]} className="flex-1 bg-transparent px-3 py-3 text-gray-100 placeholder-gray-500 focus:outline-none text-base" disabled={isLoading} />
          )}
          <button type="submit" disabled={isLoading || (inputType === 'image' ? !imageBase64 : !input.trim())}
            className="btn-primary flex items-center gap-2 px-5 py-3 disabled:opacity-50 disabled:cursor-not-allowed">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Search className="w-5 h-5" /><span className="hidden sm:inline">Analyze</span></>}
          </button>
        </div>
      </form>
      {inputType !== 'image' && (
        <div className="flex flex-wrap gap-2 justify-center">
          {[
            { text: 'Did India win the 2024 T20 World Cup?', type: 'text' },
            { text: 'Is WHO recommending ban on artificial sweeteners?', type: 'text' },
            { text: 'https://www.bbc.com/news', type: 'url' },
            { text: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', type: 'youtube' },
          ].map(({ text, type }) => (
            <button key={text} type="button" onClick={() => { setInput(text); setInputType(type); }}
              className="px-3 py-1.5 text-xs bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/15 rounded-full text-gray-400 hover:text-gray-200 transition-all">
              {text.length > 45 ? text.substring(0, 45) + '...' : text}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

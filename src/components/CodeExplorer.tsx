import React, { useState } from 'react';
import {
  FileCode,
  Folder,
  Download,
  Copy,
  Check,
  Search,
  Terminal,
  ShieldCheck,
  Cpu,
  Layers
} from 'lucide-react';
import JSZip from 'jszip';
import { BOT_FILES, BotFileItem } from '../data/botFiles';

export const CodeExplorer: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<BotFileItem>(BOT_FILES[0]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [copied, setCopied] = useState<boolean>(false);
  const [isZipping, setIsZipping] = useState<boolean>(false);

  const filteredFiles = BOT_FILES.filter((f) => {
    const matchesSearch =
      f.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || f.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const handleCopyCode = () => {
    navigator.clipboard.writeText(selectedFile.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadZip = async () => {
    setIsZipping(true);
    try {
      const zip = new JSZip();
      const folder = zip.folder('CosmicKiBaddie');

      for (const file of BOT_FILES) {
        folder?.file(file.path, file.content);
      }

      const blob = await zip.generateAsync({ type: 'blob' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'CosmicKiBaddie-Bot-Production.zip';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to generate ZIP:', err);
    } finally {
      setIsZipping(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-13rem)] min-h-[580px] bg-[#1e1f29] rounded-xl overflow-hidden border border-purple-900/40 shadow-2xl">
      {/* Top Bar with Downloader */}
      <div className="flex items-center justify-between px-5 py-3.5 bg-[#171821] border-b border-purple-950/60">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-600/20 text-purple-400 border border-purple-500/30">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-white text-base flex items-center gap-2">
              CosmicKiBaddie / Codebase Directory
              <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded font-mono border border-emerald-500/40">
                17 Cogs Verified
              </span>
            </h2>
            <p className="text-xs text-gray-400">
              Modular discord.py v2.3+ architecture • SQLite persistence • Zero hardcoded tokens
            </p>
          </div>
        </div>

        <button
          onClick={handleDownloadZip}
          disabled={isZipping}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-lg text-sm font-semibold transition active:scale-95 shadow-lg shadow-purple-900/30 disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          {isZipping ? 'Packaging ZIP...' : 'Download Bot (.zip)'}
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Files List */}
        <div className="w-72 bg-[#171821] border-r border-purple-950/60 flex flex-col">
          {/* Search & Filter */}
          <div className="p-3 border-b border-purple-950/50 space-y-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
              <input
                type="text"
                placeholder="Search bot modules..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#1e1f29] border border-purple-950 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
              />
            </div>
            <div className="flex gap-1 overflow-x-auto text-[11px] pb-1">
              {['all', 'core', 'cogs', 'config', 'scripts'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  className={`px-2 py-1 rounded capitalize transition shrink-0 ${
                    categoryFilter === cat
                      ? 'bg-purple-600 text-white font-medium'
                      : 'bg-[#232433] text-gray-400 hover:text-white'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Files Tree */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {filteredFiles.map((file) => {
              const isSelected = selectedFile.path === file.path;
              return (
                <button
                  key={file.path}
                  onClick={() => setSelectedFile(file)}
                  className={`w-full flex items-start gap-2.5 p-2 rounded-lg text-left transition ${
                    isSelected
                      ? 'bg-purple-950/40 text-purple-200 border border-purple-700/50 font-medium'
                      : 'text-gray-300 hover:bg-[#232433]/70 hover:text-white'
                  }`}
                >
                  <FileCode className={`w-4 h-4 mt-0.5 shrink-0 ${isSelected ? 'text-purple-400' : 'text-gray-500'}`} />
                  <div className="overflow-hidden">
                    <div className="text-xs font-mono truncate">{file.path}</div>
                    <div className="text-[10px] text-gray-400 truncate mt-0.5">{file.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Code Viewer */}
        <div className="flex-1 flex flex-col bg-[#13141c] overflow-hidden">
          {/* File Header */}
          <div className="px-5 py-2.5 bg-[#171821] border-b border-purple-950/60 flex items-center justify-between text-xs text-gray-400">
            <div className="flex items-center gap-2">
              <span className="font-mono text-purple-300 font-semibold">{selectedFile.path}</span>
              <span>•</span>
              <span>{selectedFile.description}</span>
            </div>
            <button
              onClick={handleCopyCode}
              className="flex items-center gap-1.5 bg-[#232433] hover:bg-purple-900/40 text-gray-200 hover:text-white px-3 py-1.5 rounded transition text-xs border border-purple-900/40"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied!' : 'Copy Code'}
            </button>
          </div>

          {/* Code Body */}
          <div className="flex-1 overflow-auto p-5 font-mono text-xs text-purple-100 leading-relaxed bg-[#0d0e15] select-text">
            <pre className="whitespace-pre">
              <code>{selectedFile.content}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

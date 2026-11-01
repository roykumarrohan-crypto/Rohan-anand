/**
 * Cosmic ki baddie - Web Management Studio & Discord Simulator
 * Dedicated to Side Quest Studio
 */

import React, { useState } from 'react';
import {
  Sparkles,
  MessageSquare,
  FileCode,
  Database,
  Rocket,
  Shield,
  Ticket,
  Bot,
  Layers,
  ChevronRight,
  ExternalLink,
  Award
} from 'lucide-react';
import { DiscordStudio } from './components/DiscordStudio';
import { CodeExplorer } from './components/CodeExplorer';
import { DatabaseViewer } from './components/DatabaseViewer';
import { DeploymentGuide } from './components/DeploymentGuide';

export default function App() {
  const [activeTab, setActiveTab] = useState<'simulator' | 'code' | 'database' | 'deployment'>('simulator');

  return (
    <div className="min-h-screen bg-[#0e0f17] text-gray-100 flex flex-col font-sans selection:bg-purple-600 selection:text-white">
      {/* Top Cosmic Header */}
      <header className="bg-[#151622] border-b border-purple-950/70 sticky top-0 z-40 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Server Badge */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-cyan-400 p-0.5 shadow-lg shadow-purple-900/40">
              <div className="w-full h-full bg-[#151622] rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-purple-400 animate-pulse" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-extrabold text-white text-base tracking-tight flex items-center gap-1.5">
                  Cosmic ki baddie
                  <span className="text-[10px] bg-gradient-to-r from-purple-500 to-indigo-500 text-white font-mono px-1.5 py-0.5 rounded font-bold uppercase shadow-sm">
                    Production
                  </span>
                </h1>
              </div>
              <div className="text-xs text-gray-400 flex items-center gap-1.5">
                <span>Dedicated Engine for</span>
                <span className="text-purple-300 font-medium">Side Quest Studio</span>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 bg-[#1a1b2a] p-1 rounded-xl border border-purple-950/60">
            <button
              onClick={() => setActiveTab('simulator')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'simulator'
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-900/40'
                  : 'text-gray-400 hover:text-white hover:bg-purple-950/40'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Discord Simulator</span>
            </button>

            <button
              onClick={() => setActiveTab('code')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'code'
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-900/40'
                  : 'text-gray-400 hover:text-white hover:bg-purple-950/40'
              }`}
            >
              <FileCode className="w-3.5 h-3.5" />
              <span>Python Codebase</span>
            </button>

            <button
              onClick={() => setActiveTab('database')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'database'
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-900/40'
                  : 'text-gray-400 hover:text-white hover:bg-purple-950/40'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>SQLite Schema</span>
            </button>

            <button
              onClick={() => setActiveTab('deployment')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'deployment'
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-900/40'
                  : 'text-gray-400 hover:text-white hover:bg-purple-950/40'
              }`}
            >
              <Rocket className="w-3.5 h-3.5" />
              <span>Deployment & Invite</span>
            </button>
          </nav>

          {/* Quick System Status */}
          <div className="hidden lg:flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5 bg-[#1a1b2a] border border-purple-900/40 px-3 py-1.5 rounded-lg">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-gray-300 font-mono">Gateway Ready</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col gap-6">
        {/* Metric Badges */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3.5 bg-[#151622] rounded-xl border border-purple-950/60 flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-purple-900/30 text-purple-400 border border-purple-800/30">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs text-gray-400">Modular Cogs</div>
              <div className="text-sm font-bold text-white">17 Verified Modules</div>
            </div>
          </div>

          <div className="p-3.5 bg-[#151622] rounded-xl border border-purple-950/60 flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-emerald-900/30 text-emerald-400 border border-emerald-800/30">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs text-gray-400">Anti-Nuke Engine</div>
              <div className="text-sm font-bold text-white">Triple Safeguard</div>
            </div>
          </div>

          <div className="p-3.5 bg-[#151622] rounded-xl border border-purple-950/60 flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-cyan-900/30 text-cyan-400 border border-cyan-800/30">
              <Ticket className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs text-gray-400">Support System</div>
              <div className="text-sm font-bold text-white">Persistent Buttons</div>
            </div>
          </div>

          <div className="p-3.5 bg-[#151622] rounded-xl border border-purple-950/60 flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-900/30 text-amber-400 border border-amber-800/30">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs text-gray-400">Persistence</div>
              <div className="text-sm font-bold text-white">SQLite Async WAL</div>
            </div>
          </div>
        </div>

        {/* Tab Panes */}
        {activeTab === 'simulator' && <DiscordStudio />}
        {activeTab === 'code' && <CodeExplorer />}
        {activeTab === 'database' && <DatabaseViewer />}
        {activeTab === 'deployment' && <DeploymentGuide />}
      </main>

      {/* Footer */}
      <footer className="bg-[#12131c] border-t border-purple-950/50 py-4 text-center text-xs text-gray-500">
        Cosmic ki baddie • Built with discord.py & aiosqlite for Side Quest Studio
      </footer>
    </div>
  );
}

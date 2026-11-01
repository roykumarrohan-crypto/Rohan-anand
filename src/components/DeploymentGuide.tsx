import React, { useState } from 'react';
import {
  ExternalLink,
  ShieldCheck,
  Server,
  Key,
  CheckCircle,
  Copy,
  Terminal,
  HelpCircle,
  Check
} from 'lucide-react';

export const DeploymentGuide: React.FC = () => {
  const [clientId, setClientId] = useState<string>('123456789012345678');
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  const inviteUrl = `https://discord.com/oauth2/authorize?client_id=${clientId.trim() || 'YOUR_CLIENT_ID'}&permissions=8&scope=bot%20applications.commands`;

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(id);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-13rem)] min-h-[580px] bg-[#1e1f29] rounded-xl overflow-hidden border border-purple-900/40 shadow-2xl overflow-y-auto p-6 space-y-6">
      {/* Top Banner */}
      <div className="p-5 bg-gradient-to-r from-purple-950/60 to-indigo-950/60 rounded-xl border border-purple-800/40">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Server className="w-6 h-6 text-purple-400" />
          Discord Developer Portal & 24/7 Hosting Guide
        </h2>
        <p className="text-sm text-gray-300 mt-1">
          Follow this 3-step checklist to connect <strong>Cosmic ki baddie</strong> to Discord and deploy it permanently for <strong>Side Quest Studio</strong>.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Step 1: Discord Dev Portal */}
        <div className="p-5 bg-[#171821] rounded-xl border border-purple-950/60 space-y-4">
          <div className="flex items-center gap-3">
            <span className="w-7 h-7 rounded-full bg-purple-600 text-white font-bold flex items-center justify-center text-xs">
              1
            </span>
            <h3 className="font-bold text-white text-base">Discord Developer Portal Setup</h3>
          </div>

          <p className="text-xs text-gray-400 leading-relaxed">
            Create your Discord Application and enable the mandatory privileged intents.
          </p>

          <ol className="text-xs text-gray-300 space-y-2 list-decimal list-inside">
            <li>
              Visit the{' '}
              <a
                href="https://discord.com/developers/applications"
                target="_blank"
                rel="noreferrer"
                className="text-purple-400 hover:underline font-semibold inline-flex items-center gap-1"
              >
                Discord Developer Portal <ExternalLink className="w-3 h-3" />
              </a>
            </li>
            <li>Click <strong>New Application</strong> and name it <code className="text-purple-300">Cosmic ki baddie</code>.</li>
            <li>Navigate to the <strong>Bot</strong> tab and click <strong>Reset Token</strong>. Copy it for your <code className="text-purple-300">.env</code>.</li>
            <li>
              Scroll down to <strong>Privileged Gateway Intents</strong> and enable:
              <div className="mt-1 pl-4 space-y-1 text-emerald-400 font-mono text-[11px]">
                <div>✅ Server Members Intent (For welcome cards & autorole)</div>
                <div>✅ Message Content Intent (For prefix commands & autoresponder)</div>
                <div>✅ Presence Intent (For member tracking)</div>
              </div>
            </li>
          </ol>
        </div>

        {/* Step 2: Invite URL Generator */}
        <div className="p-5 bg-[#171821] rounded-xl border border-purple-950/60 space-y-4">
          <div className="flex items-center gap-3">
            <span className="w-7 h-7 rounded-full bg-purple-600 text-white font-bold flex items-center justify-center text-xs">
              2
            </span>
            <h3 className="font-bold text-white text-base">Generate Bot Invite Link</h3>
          </div>

          <p className="text-xs text-gray-400">
            Paste your <strong>Application ID / Client ID</strong> below to generate the exact OAuth2 invite link with Administrator & Slash Command scopes for Side Quest Studio.
          </p>

          <div>
            <label className="block text-xs uppercase font-bold text-gray-400 mb-1">
              Application ID (Client ID)
            </label>
            <input
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="e.g. 123456789012345678"
              className="w-full bg-[#1e1f29] border border-purple-950 rounded p-2 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
            />
          </div>

          <div className="p-3 bg-[#13141c] rounded-lg border border-purple-950/60">
            <div className="text-[11px] text-gray-400 mb-1">Generated Invite URL:</div>
            <div className="text-xs text-purple-300 font-mono break-all mb-2">{inviteUrl}</div>
            <a
              href={inviteUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-[#5865f2] hover:bg-[#4752c4] text-white rounded text-xs font-semibold transition"
            >
              Authorize Bot to Side Quest Studio <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </div>

      {/* Step 3: 24/7 Hosting Scripts */}
      <div className="p-5 bg-[#171821] rounded-xl border border-purple-950/60 space-y-4">
        <div className="flex items-center gap-3">
          <span className="w-7 h-7 rounded-full bg-purple-600 text-white font-bold flex items-center justify-center text-xs">
            3
          </span>
          <h3 className="font-bold text-white text-base">24/7 Production Deployment Commands</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Linux VPS / systemd */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-gray-300 uppercase">Option A: Linux VPS with systemd</h4>
            <div className="bg-[#13141c] p-3 rounded-lg border border-purple-950 font-mono text-xs text-purple-200 relative group">
              <button
                onClick={() =>
                  copyToClipboard(
                    `chmod +x start.sh\n./start.sh`,
                    'vps'
                  )
                }
                className="absolute right-2 top-2 p-1.5 bg-[#232433] rounded hover:text-white text-gray-400"
              >
                {copiedCmd === 'vps' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
              <pre className="text-xs leading-relaxed">
{`# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env
cp .env.example .env
nano .env

# 3. Launch with start.sh
chmod +x start.sh
./start.sh`}
              </pre>
            </div>
          </div>

          {/* Railway / Render */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-gray-300 uppercase">Option B: Railway / Render Worker</h4>
            <div className="bg-[#13141c] p-3 rounded-lg border border-purple-950 font-mono text-xs text-purple-200 relative group">
              <button
                onClick={() =>
                  copyToClipboard(
                    `worker: python3 main.py`,
                    'railway'
                  )
                }
                className="absolute right-2 top-2 p-1.5 bg-[#232433] rounded hover:text-white text-gray-400"
              >
                {copiedCmd === 'railway' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
              <pre className="text-xs leading-relaxed">
{`# Procfile for Railway or Heroku
worker: python3 main.py

# Set Environment Variables in UI:
DISCORD_TOKEN=your_token_here
MAIN_SERVER_NAME="Side Quest Studio"`}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

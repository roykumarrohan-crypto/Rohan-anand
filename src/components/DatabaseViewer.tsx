import React, { useState } from 'react';
import { Database, Table, Shield, Key, Search, RefreshCw, HardDrive } from 'lucide-react';

interface TableDefinition {
  name: string;
  category: string;
  description: string;
  primaryKey: string;
  columns: { name: string; type: string; desc: string }[];
  sampleRows: Record<string, any>[];
}

const DB_TABLES: TableDefinition[] = [
  {
    name: 'guild_config',
    category: 'Core',
    description: 'Server specific settings, prefix, channel mappings, and role IDs.',
    primaryKey: 'guild_id',
    columns: [
      { name: 'guild_id', type: 'INTEGER', desc: 'Discord Server ID (Primary Key)' },
      { name: 'prefix', type: 'TEXT', desc: 'Custom command prefix (Default: !)' },
      { name: 'welcome_channel_id', type: 'INTEGER', desc: 'Channel ID for greeting cards' },
      { name: 'mod_log_channel_id', type: 'INTEGER', desc: 'Audit logging for punishments' },
      { name: 'ticket_category_id', type: 'INTEGER', desc: 'Category under which tickets are opened' },
      { name: 'ticket_support_role_id', type: 'INTEGER', desc: 'Staff role allowed to view & claim tickets' },
      { name: 'autorole_id', type: 'INTEGER', desc: 'Role automatically granted to newcomers' },
      { name: 'safe_mode', type: 'INTEGER', desc: 'Flag 1/0 restricting sensitive bot actions' },
    ],
    sampleRows: [
      {
        guild_id: '995142079491',
        prefix: '!',
        welcome_channel_id: '12450091028',
        mod_log_channel_id: '12450091040',
        ticket_category_id: '12450091055',
        ticket_support_role_id: '12450091099',
        autorole_id: '12450091012',
        safe_mode: 0,
      },
    ],
  },
  {
    name: 'command_permissions',
    category: 'Permissions',
    description: 'Dynamic per-command role overrides configured in-Discord without editing Python code.',
    primaryKey: 'guild_id, entity_id, command_name',
    columns: [
      { name: 'guild_id', type: 'INTEGER', desc: 'Server ID' },
      { name: 'entity_type', type: 'TEXT', desc: "'role' or 'user'" },
      { name: 'entity_id', type: 'INTEGER', desc: 'Role or User Snowflake ID' },
      { name: 'command_name', type: 'TEXT', desc: 'Name of the bot command (e.g. ban, ticket)' },
      { name: 'access', type: 'INTEGER', desc: '1 = Allow, 0 = Deny' },
    ],
    sampleRows: [
      { guild_id: '995142079491', entity_type: 'role', entity_id: '12450091099', command_name: 'ban', access: 1 },
      { guild_id: '995142079491', entity_type: 'role', entity_id: '12450091012', command_name: 'purge', access: 0 },
      { guild_id: '995142079491', entity_type: 'role', entity_id: '12450091088', command_name: 'ticket', access: 1 },
    ],
  },
  {
    name: 'moderation_records',
    category: 'Moderation',
    description: 'Immutable historical audit logs of bans, kicks, timeouts, and unbans.',
    primaryKey: 'id',
    columns: [
      { name: 'id', type: 'INTEGER AUTOINCREMENT', desc: 'Unique Case ID' },
      { name: 'guild_id', type: 'INTEGER', desc: 'Server ID' },
      { name: 'target_id', type: 'INTEGER', desc: 'Punished User ID' },
      { name: 'target_name', type: 'TEXT', desc: 'Username string at time of action' },
      { name: 'moderator_id', type: 'INTEGER', desc: 'Responsible Staff Member ID' },
      { name: 'action', type: 'TEXT', desc: 'BAN, KICK, TIMEOUT, UNBAN' },
      { name: 'reason', type: 'TEXT', desc: 'Moderator supplied rationale' },
      { name: 'timestamp', type: 'REAL', desc: 'Unix Epoch timestamp' },
    ],
    sampleRows: [
      {
        id: 1,
        guild_id: '995142079491',
        target_id: '4892109481',
        target_name: 'RogueSpammer#1029',
        moderator_id: '1092819283',
        action: 'BAN',
        reason: 'Severe phishing links in general',
        timestamp: 1730462400,
      },
      {
        id: 2,
        guild_id: '995142079491',
        target_id: '7829102931',
        target_name: 'NoisyUser#4401',
        moderator_id: '1092819283',
        action: 'TIMEOUT (60m)',
        reason: 'Excessive caps spam in vc-chat',
        timestamp: 1730463200,
      },
    ],
  },
  {
    name: 'tickets',
    category: 'Support',
    description: 'Active and archived support tickets with transcripts.',
    primaryKey: 'id',
    columns: [
      { name: 'id', type: 'INTEGER AUTOINCREMENT', desc: 'Ticket Case Number' },
      { name: 'channel_id', type: 'INTEGER', desc: 'Private Discord Channel ID' },
      { name: 'creator_id', type: 'INTEGER', desc: 'Ticket opener' },
      { name: 'claimer_id', type: 'INTEGER', desc: 'Assigned staff handler' },
      { name: 'status', type: 'TEXT', desc: "'open' or 'closed'" },
      { name: 'transcript_text', type: 'TEXT', desc: 'Archived text log of messages' },
    ],
    sampleRows: [
      {
        id: 101,
        channel_id: '12499182901',
        creator_id: '5829102941',
        claimer_id: '1092819283',
        status: 'open',
        transcript_text: '[2026-11-01] User opened ticket: perk issue...',
      },
    ],
  },
  {
    name: 'autoresponders',
    category: 'Automation',
    description: 'Deterministic rule-based keyword triggers with match types and cooldowns.',
    primaryKey: 'id',
    columns: [
      { name: 'id', type: 'INTEGER', desc: 'Rule ID' },
      { name: 'trigger_text', type: 'TEXT', desc: 'Keyword or phrase' },
      { name: 'match_type', type: 'TEXT', desc: "'exact', 'contains', 'startswith'" },
      { name: 'response_text', type: 'TEXT', desc: 'Message or embed text to send' },
      { name: 'cooldown_sec', type: 'INTEGER', desc: 'Anti-spam cooldown interval' },
      { name: 'is_enabled', type: 'INTEGER', desc: '1 = active, 0 = disabled' },
    ],
    sampleRows: [
      { id: 1, trigger_text: 'hello', match_type: 'exact', response_text: 'Welcome to Side Quest Studio! ✨', cooldown_sec: 5, is_enabled: 1 },
      { id: 2, trigger_text: 'rules', match_type: 'contains', response_text: 'Check out our server rules in #rules.', cooldown_sec: 5, is_enabled: 1 },
      { id: 3, trigger_text: 'help', match_type: 'exact', response_text: 'Need assistance? Open a support ticket!', cooldown_sec: 5, is_enabled: 1 },
    ],
  },
  {
    name: 'anti_nuke_config',
    category: 'Security',
    description: 'Threshold limits and time windows to prevent rogue administrators or bot tokens from nuking channels.',
    primaryKey: 'guild_id',
    columns: [
      { name: 'channel_delete_threshold', type: 'INTEGER', desc: 'Max channel deletes per window (Default: 3)' },
      { name: 'role_delete_threshold', type: 'INTEGER', desc: 'Max role deletes per window (Default: 3)' },
      { name: 'kick_ban_threshold', type: 'INTEGER', desc: 'Max bans or kicks per window (Default: 3)' },
      { name: 'window_seconds', type: 'INTEGER', desc: 'Sliding window in seconds (Default: 60s)' },
      { name: 'protection_mode', type: 'TEXT', desc: 'SAFE_MODE, SERVER_PROTECTION, EMERGENCY_LOCKDOWN' },
    ],
    sampleRows: [
      {
        channel_delete_threshold: 3,
        role_delete_threshold: 3,
        kick_ban_threshold: 3,
        window_seconds: 60,
        protection_mode: 'SERVER_PROTECTION',
      },
    ],
  },
];

export const DatabaseViewer: React.FC = () => {
  const [selectedTable, setSelectedTable] = useState<TableDefinition>(DB_TABLES[0]);
  const [search, setSearch] = useState<string>('');

  const filteredTables = DB_TABLES.filter(
    (t) => t.name.toLowerCase().includes(search.toLowerCase()) || t.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col h-[calc(100vh-13rem)] min-h-[580px] bg-[#1e1f29] rounded-xl overflow-hidden border border-purple-900/40 shadow-2xl">
      {/* Top Header */}
      <div className="flex items-center justify-between px-5 py-3.5 bg-[#171821] border-b border-purple-950/60">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-600/20 text-cyan-400 border border-cyan-500/30">
            <HardDrive className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-white text-base flex items-center gap-2">
              SQLite Database Architecture & Schemas
              <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded font-mono border border-purple-500/40">
                WAL Mode Enabled
              </span>
            </h2>
            <p className="text-xs text-gray-400">
              Persistent storage path: <code className="text-cyan-300">data/cosmic_bot.db</code> (Async aiosqlite connection pool)
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Tables Sidebar */}
        <div className="w-64 bg-[#171821] border-r border-purple-950/60 flex flex-col">
          <div className="p-3 border-b border-purple-950/50">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
              <input
                type="text"
                placeholder="Search tables..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-[#1e1f29] border border-purple-950 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {filteredTables.map((t) => {
              const isSelected = selectedTable.name === t.name;
              return (
                <button
                  key={t.name}
                  onClick={() => setSelectedTable(t)}
                  className={`w-full flex items-center justify-between p-2.5 rounded-lg text-left transition ${
                    isSelected
                      ? 'bg-cyan-950/40 text-cyan-200 border border-cyan-700/50 font-medium'
                      : 'text-gray-300 hover:bg-[#232433] hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Table className={`w-4 h-4 ${isSelected ? 'text-cyan-400' : 'text-gray-500'}`} />
                    <span className="text-xs font-mono">{t.name}</span>
                  </div>
                  <span className="text-[10px] bg-[#232433] text-gray-400 px-1.5 py-0.5 rounded">
                    {t.category}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Table Details & Data Viewer */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#13141c]">
          {/* Table Summary Card */}
          <div className="p-4 bg-[#1b1c26] rounded-xl border border-purple-950/60">
            <div className="flex items-baseline justify-between mb-2">
              <h3 className="text-lg font-bold text-white font-mono flex items-center gap-2">
                <Database className="w-5 h-5 text-cyan-400" />
                table: {selectedTable.name}
              </h3>
              <span className="text-xs text-gray-400 font-mono">
                Primary Key: <span className="text-amber-400">{selectedTable.primaryKey}</span>
              </span>
            </div>
            <p className="text-xs text-gray-300">{selectedTable.description}</p>
          </div>

          {/* Columns Schema */}
          <div className="space-y-2">
            <h4 className="text-xs uppercase font-bold text-gray-400 tracking-wider">Table Columns</h4>
            <div className="overflow-x-auto rounded-lg border border-purple-950/60">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#1b1c26] text-gray-400 font-semibold uppercase text-[10px] border-b border-purple-950/60">
                  <tr>
                    <th className="px-4 py-2.5">Column Name</th>
                    <th className="px-4 py-2.5">Data Type</th>
                    <th className="px-4 py-2.5">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-purple-950/40 text-gray-300 font-mono">
                  {selectedTable.columns.map((col) => (
                    <tr key={col.name} className="hover:bg-purple-950/20">
                      <td className="px-4 py-2 text-cyan-300 font-semibold">{col.name}</td>
                      <td className="px-4 py-2 text-amber-300">{col.type}</td>
                      <td className="px-4 py-2 font-sans text-gray-400">{col.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Active Sample Rows */}
          <div className="space-y-2">
            <h4 className="text-xs uppercase font-bold text-gray-400 tracking-wider">
              Live Mock Records ({selectedTable.sampleRows.length})
            </h4>
            <div className="overflow-x-auto rounded-lg border border-purple-950/60">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#1b1c26] text-gray-400 uppercase text-[10px] border-b border-purple-950/60">
                  <tr>
                    {selectedTable.columns.map((col) => (
                      <th key={col.name} className="px-4 py-2.5 truncate">
                        {col.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-purple-950/40 text-gray-200">
                  {selectedTable.sampleRows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-purple-950/20">
                      {selectedTable.columns.map((col) => (
                        <td key={col.name} className="px-4 py-2.5 truncate max-w-xs text-xs">
                          {String(row[col.name] ?? '-')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

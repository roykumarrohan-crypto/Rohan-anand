import React, { useState, useRef, useEffect } from 'react';
import {
  Hash,
  Volume2,
  Bell,
  Pin,
  Users,
  Search,
  Send,
  Sparkles,
  Shield,
  Ticket,
  Gift,
  BarChart2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Lock,
  Unlock,
  PlusCircle,
  ArrowRight
} from 'lucide-react';
import { matchAutoresponder, parseDurationToSeconds, calculatePollTally } from '../logic/simulatorEngine';

interface DiscordMessage {
  id: string;
  channelId: string;
  author: {
    name: string;
    avatar: string;
    isBot?: boolean;
    roleColor?: string;
    tag?: string;
  };
  timestamp: string;
  content?: string;
  embed?: {
    title?: string;
    description?: string;
    color?: string; // hex
    fields?: { name: string; value: string; inline?: boolean }[];
    footer?: string;
    thumbnail?: string;
  };
  components?: {
    type: 'buttons' | 'select';
    buttons?: {
      id: string;
      label: string;
      style: 'primary' | 'secondary' | 'success' | 'danger';
      emoji?: string;
      disabled?: boolean;
      onClick: () => void;
    }[];
    select?: {
      placeholder: string;
      options: { label: string; value: string; emoji?: string; desc?: string }[];
      onSelect: (val: string) => void;
    };
  }[];
}

// Simple Discord-style formatting helper
export function formatDiscordText(text?: string): React.ReactNode {
  if (!text) return null;

  // Split lines
  const lines = text.split('\n');
  return (
    <div className="space-y-1">
      {lines.map((line, lIdx) => {
        // Regex replace mentions, bold, and code
        const parts = line.split(/(<@[^>]+>|<#rules>|<#mod-logs>|<#announcements>|<#welcome-gate>|<#support-tickets>|<#bot-commands>|<#polls-giveaways>|\*\*[^*]+\*\*|`[^`]+`)/g);

        return (
          <div key={lIdx} className="min-h-[1.25rem]">
            {parts.map((part, pIdx) => {
              if (part.startsWith('<@') && part.endsWith('>')) {
                const name = part.slice(2, -1);
                return (
                  <span
                    key={pIdx}
                    className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded bg-[#5865f2]/20 hover:bg-[#5865f2]/30 text-[#c9cdfb] font-medium text-xs cursor-pointer transition"
                  >
                    @{name}
                  </span>
                );
              }
              if (part.startsWith('<#') && part.endsWith('>')) {
                const ch = part.slice(2, -1);
                return (
                  <span
                    key={pIdx}
                    className="inline-flex items-center gap-0.5 px-1.5 py-0.5 mx-0.5 rounded bg-[#4e5058]/40 hover:bg-[#4e5058]/70 text-[#949ba4] hover:text-white font-medium text-xs cursor-pointer transition"
                  >
                    #{ch}
                  </span>
                );
              }
              if (part.startsWith('**') && part.endsWith('**')) {
                return (
                  <strong key={pIdx} className="font-bold text-white">
                    {part.slice(2, -2)}
                  </strong>
                );
              }
              if (part.startsWith('`') && part.endsWith('`')) {
                return (
                  <code
                    key={pIdx}
                    className="bg-[#1e1f22] text-[#e0e1e5] px-1.5 py-0.5 rounded text-[11px] font-mono border border-[#3f4147]/50"
                  >
                    {part.slice(1, -1)}
                  </code>
                );
              }
              return <span key={pIdx}>{part}</span>;
            })}
          </div>
        );
      })}
    </div>
  );
}

export const DiscordStudio: React.FC = () => {
  const [activeChannelId, setActiveChannelId] = useState<string>('bot-commands');
  const [inputText, setInputText] = useState<string>('');
  const [ticketModalOpen, setTicketModalOpen] = useState<boolean>(false);
  const [ticketSubject, setTicketSubject] = useState<string>('');
  const [ticketDetails, setTicketDetails] = useState<string>('');
  const [giveawayEntries, setGiveawayEntries] = useState<number>(14);
  const [hasEnteredGiveaway, setHasEnteredGiveaway] = useState<boolean>(false);
  const [pollVotes, setPollVotes] = useState<Record<number, number>>({ 0: 12, 1: 8, 2: 4 });
  const [userVotedOption, setUserVotedOption] = useState<number | null>(null);
  const [safeModeActive, setSafeModeActive] = useState<boolean>(false);
  const [channels, setChannels] = useState<ChannelItem[]>([
    { id: 'announcements', name: 'announcements', type: 'text', topic: 'Official Side Quest Studio updates' },
    { id: 'welcome-gate', name: 'welcome-gate', type: 'text', topic: 'Traveler greetings and autorole assignment' },
    { id: 'general', name: 'general', type: 'text', topic: 'Cosmic community discussions & gaming' },
    { id: 'rules', name: 'rules', type: 'text', topic: 'Side Quest Studio community code of conduct' },
    { id: 'bot-commands', name: 'bot-commands', type: 'text', topic: 'Run /help, /dashboard, and bot commands here' },
    { id: 'support-tickets', name: 'support-tickets', type: 'text', topic: 'Interactive ticket launcher panel' },
    { id: 'polls-giveaways', name: 'polls-giveaways', type: 'text', topic: 'Community votes and active giveaways' },
    { id: 'mod-logs', name: 'mod-logs', type: 'text', topic: 'Audit log dispatch channel' },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<DiscordMessage[]>([
    {
      id: 'm1',
      channelId: 'welcome-gate',
      author: {
        name: 'Cosmic ki baddie',
        avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
        isBot: true,
        roleColor: '#8a2be2',
        tag: 'BOT',
      },
      timestamp: 'Today at 6:45 PM',
      content: '@TravelerNewbie',
      embed: {
        title: '✨ Welcome to Side Quest Studio!',
        description:
          'Another side quest unlocked! ✨\n\nWelcome <@TravelerNewbie> to **Side Quest Studio**!\n\nYour adventure starts here. Explore the channels, meet the community, and find your people.\n\nDon\'t forget to check out the rules!',
        color: '#8A2BE2',
        footer: 'Member #1,420 • Side Quest Studio',
      },
    },
    {
      id: 'm2',
      channelId: 'support-tickets',
      author: {
        name: 'Cosmic ki baddie',
        avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
        isBot: true,
        roleColor: '#8a2be2',
        tag: 'BOT',
      },
      timestamp: 'Today at 6:50 PM',
      embed: {
        title: '🌌 Side Quest Studio • Support Hub',
        description:
          'Need assistance with server perks, questions, or reporting a rule violation?\n\nClick the button below to start a private ticket with our staff team.\n\n• **Guidelines:** Be respectful, state your issue clearly with screenshots if applicable.',
        color: '#8A2BE2',
        footer: 'Cosmic ki baddie • Ticket Manager',
      },
      components: [
        {
          type: 'buttons',
          buttons: [
            {
              id: 'btn-open-ticket',
              label: 'Open Support Ticket',
              style: 'primary',
              emoji: '🎫',
              onClick: () => setTicketModalOpen(true),
            },
            {
              id: 'btn-report-player',
              label: 'Report Player / Issue',
              style: 'danger',
              emoji: '🚨',
              onClick: () => setTicketModalOpen(true),
            },
          ],
        },
      ],
    },
    {
      id: 'm3',
      channelId: 'polls-giveaways',
      author: {
        name: 'Cosmic ki baddie',
        avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
        isBot: true,
        roleColor: '#8a2be2',
        tag: 'BOT',
      },
      timestamp: 'Today at 6:52 PM',
      embed: {
        title: '🎉 GIVEAWAY: Discord Nitro (1 Month)',
        description:
          'Click the button below to participate!\n\n**Winners:** 1\n**Hosted by:** <@ServerOwner>\n**Ends:** in 2 hours',
        color: '#8A2BE2',
        footer: 'Side Quest Studio • Cosmic Giveaways',
      },
      components: [
        {
          type: 'buttons',
          buttons: [
            {
              id: 'btn-giveaway-enter',
              label: 'Enter Giveaway 🎉',
              style: 'primary',
              emoji: '🎉',
              onClick: () => handleGiveawayEnter(),
            },
          ],
        },
      ],
    },
    {
      id: 'm4',
      channelId: 'bot-commands',
      author: {
        name: 'Cosmic ki baddie',
        avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
        isBot: true,
        roleColor: '#8a2be2',
        tag: 'BOT',
      },
      timestamp: 'Today at 7:00 PM',
      embed: {
        title: '🌌 Cosmic ki baddie • Command Directory',
        description:
          'Welcome to **Side Quest Studio\'s** primary server management and automation engine!\n\n• **Current Prefix:** `!`\n• **Slash Commands:** Enabled (`/`)\n\nTry sending `!help`, `/dashboard`, `/setup`, `/ban`, `/purge`, or chat trigger words like `hello` or `rules`!',
        color: '#8A2BE2',
        footer: 'Ready for commands • v2.4.0-Production',
      },
    },
  ]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeChannelId]);

  const handleGiveawayEnter = () => {
    if (hasEnteredGiveaway) return;
    setHasEnteredGiveaway(true);
    setGiveawayEntries((prev) => prev + 1);

    const botResponse: DiscordMessage = {
      id: `bot-${Date.now()}`,
      channelId: 'polls-giveaways',
      author: {
        name: 'Cosmic ki baddie',
        avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
        isBot: true,
        roleColor: '#8a2be2',
        tag: 'BOT',
      },
      timestamp: 'Just now',
      content: '🎉 <@You> You have entered the giveaway for **Discord Nitro (1 Month)**! Total entries: **' + (giveawayEntries + 1) + '**',
    };
    setMessages((prev) => [...prev, botResponse]);
  };

  const handlePollVote = (idx: number) => {
    if (userVotedOption === idx) return;
    setUserVotedOption(idx);
    setPollVotes((prev) => ({
      ...prev,
      [idx]: (prev[idx] || 0) + 1,
    }));

    const botReply: DiscordMessage = {
      id: `bot-${Date.now()}`,
      channelId: 'polls-giveaways',
      author: {
        name: 'Cosmic ki baddie',
        avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
        isBot: true,
        roleColor: '#8a2be2',
        tag: 'BOT',
      },
      timestamp: 'Just now',
      content: `✅ <@You> Your vote for option **${idx + 1}** has been cast!`,
    };
    setMessages((prev) => [...prev, botReply]);
  };

  const createTicketChannel = () => {
    if (!ticketSubject.trim()) return;
    const ticketId = Math.floor(1000 + Math.random() * 9000);
    const newChId = `ticket-${ticketId}`;
    const newChannel: ChannelItem = {
      id: newChId,
      name: `ticket-you-${ticketId}`,
      type: 'ticket',
      topic: `Support Ticket #${ticketId} | Subject: ${ticketSubject}`,
    };

    setChannels((prev) => [...prev, newChannel]);
    setActiveChannelId(newChId);
    setTicketModalOpen(false);

    const ticketWelcome: DiscordMessage = {
      id: `msg-${Date.now()}`,
      channelId: newChId,
      author: {
        name: 'Cosmic ki baddie',
        avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
        isBot: true,
        roleColor: '#8a2be2',
        tag: 'BOT',
      },
      timestamp: 'Just now',
      content: '<@You> | <@&SupportTeam>',
      embed: {
        title: `🎫 Support Ticket #${ticketId}`,
        description: `Welcome <@You>! Our Side Quest Studio support staff has been notified.\n\n**Category:** General Support\n**Subject:** ${ticketSubject}\n**Details:**\n> ${ticketDetails || 'No additional details provided.'}\n\nPlease wait for a staff member to assist you or use the controls below.`,
        color: '#8A2BE2',
        footer: 'Cosmic ki baddie • Ticket Manager',
      },
      components: [
        {
          type: 'buttons',
          buttons: [
            {
              id: 'claim-ticket',
              label: 'Claim Ticket',
              style: 'success',
              emoji: '🙋‍♂️',
              onClick: () => {
                const claimMsg: DiscordMessage = {
                  id: `claim-${Date.now()}`,
                  channelId: newChId,
                  author: {
                    name: 'Cosmic ki baddie',
                    avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
                    isBot: true,
                    roleColor: '#8a2be2',
                    tag: 'BOT',
                  },
                  timestamp: 'Just now',
                  content: '🙋‍♂️ **StaffMod** has claimed this ticket and will be assisting you.',
                };
                setMessages((prev) => [...prev, claimMsg]);
              },
            },
            {
              id: 'close-ticket',
              label: 'Close Ticket',
              style: 'secondary',
              emoji: '🔒',
              onClick: () => {
                const closeMsg: DiscordMessage = {
                  id: `close-${Date.now()}`,
                  channelId: newChId,
                  author: {
                    name: 'Cosmic ki baddie',
                    avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
                    isBot: true,
                    roleColor: '#8a2be2',
                    tag: 'BOT',
                  },
                  timestamp: 'Just now',
                  embed: {
                    title: '🔒 Ticket Closed & Archived',
                    description: `This ticket has been closed by <@You>. Transcript saved to SQLite database and dispatched to <#mod-logs>.`,
                    color: '#FFB300',
                  },
                };
                setMessages((prev) => [...prev, closeMsg]);
              },
            },
          ],
        },
      ],
    };

    setMessages((prev) => [...prev, ticketWelcome]);
    setTicketSubject('');
    setTicketDetails('');
  };

  const handleSendMessage = () => {
    const text = inputText.trim();
    if (!text) return;

    const userMsg: DiscordMessage = {
      id: `usr-${Date.now()}`,
      channelId: activeChannelId,
      author: {
        name: 'You (Traveler)',
        avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=128&auto=format&fit=crop&q=80',
        roleColor: '#00E5FF',
      },
      timestamp: 'Just now',
      content: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');

    // Process Bot Responses & Commands
    setTimeout(() => {
      processBotReaction(text, activeChannelId);
    }, 400);
  };

  const processBotReaction = (text: string, channelId: string) => {
    const lower = text.toLowerCase().trim();

    // 1. Autoresponders
    if (lower === 'hello' || lower === 'hi' || lower === 'hey') {
      sendBotMessage(channelId, 'Welcome to Side Quest Studio! ✨ Explore the channels and have fun questing!');
      return;
    }
    if (lower.includes('rules')) {
      sendBotMessage(channelId, 'Check out our server rules in <#rules>! 📜 Be respectful to all fellow travelers.');
      return;
    }
    if (lower.includes('quest') || lower.includes('side quest')) {
      sendBotMessage(channelId, '🗺️ Another side quest awaits! Type `!rank` to see your level or join a community event with `/event list`!');
      return;
    }

    // 2. Help Command (/help or !help)
    if (lower === '/help' || lower === '!help' || lower === 'help') {
      const helpMsg: DiscordMessage = {
        id: `bot-${Date.now()}`,
        channelId,
        author: {
          name: 'Cosmic ki baddie',
          avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
          isBot: true,
          roleColor: '#8a2be2',
          tag: 'BOT',
        },
        timestamp: 'Just now',
        embed: {
          title: '🌌 Cosmic ki baddie • Interactive Help Directory',
          description:
            'All features are manageable in Discord without touching Python files!\n\n**Categories Available:**\n' +
            '• 🛡️ **Moderation**: `/kick`, `/ban`, `/timeout`, `/warn`, `/slowmode`, `/lock`\n' +
            '• 🧹 **Purge**: `/purge` (by user, links, bots, attachments)\n' +
            '• 🎫 **Tickets**: `/ticket setup`, `/ticket panel`, `/ticket claim`, `/ticket close`\n' +
            '• 🛡️ **Security**: `/security status`, `/security mode`, `/security whitelist`\n' +
            '• 🎭 **Permissions**: `/permissions set role:... command:... access:true`\n' +
            '• 🎉 **Giveaways & Events**: `/giveaway start`, `/event create`\n' +
            '• 📊 **Polls**: `/poll create`, `/poll results`\n' +
            '• ⚙️ **Dashboard**: `/dashboard`, `/setup start`, `/prefix`',
          color: '#8A2BE2',
          footer: 'Side Quest Studio • Prefix: ! | Slash: /',
        },
      };
      setMessages((prev) => [...prev, helpMsg]);
      return;
    }

    // 3. /dashboard
    if (lower === '/dashboard' || lower === '!dashboard') {
      const dashMsg: DiscordMessage = {
        id: `bot-${Date.now()}`,
        channelId,
        author: {
          name: 'Cosmic ki baddie',
          avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
          isBot: true,
          roleColor: '#8a2be2',
          tag: 'BOT',
        },
        timestamp: 'Just now',
        embed: {
          title: '🌌 Side Quest Studio • Central Command Dashboard',
          description:
            'Interactive control center for server administrators.\n\n' +
            `• **Server:** Side Quest Studio (1,420 members)\n` +
            `• **Protection Mode:** \`${safeModeActive ? 'SAFE_MODE' : 'SERVER_PROTECTION'}\`\n` +
            `• **Anti-Nuke Status:** 🟢 ACTIVE (Max 3 bans/deletes per 60s)\n` +
            `• **Database:** SQLite (WAL async persistence)\n` +
            `• **Command Prefix:** \`!\``,
          color: '#8A2BE2',
          footer: 'Cosmic Management Engine',
        },
        components: [
          {
            type: 'buttons',
            buttons: [
              {
                id: 'toggle-safemode',
                label: safeModeActive ? 'Safe Mode: ON 🔒' : 'Safe Mode: OFF 🛡️',
                style: safeModeActive ? 'danger' : 'secondary',
                emoji: '🔒',
                onClick: () => {
                  setSafeModeActive((prev) => !prev);
                  sendBotMessage(
                    channelId,
                    `🛡️ Protection mode toggled: now \`${!safeModeActive ? 'SAFE_MODE' : 'SERVER_PROTECTION'}\``
                  );
                },
              },
            ],
          },
        ],
      };
      setMessages((prev) => [...prev, dashMsg]);
      return;
    }

    // 4. /ticket panel
    if (lower === '/ticket panel' || lower === '!ticket panel') {
      const ticketPanelMsg: DiscordMessage = {
        id: `bot-${Date.now()}`,
        channelId,
        author: {
          name: 'Cosmic ki baddie',
          avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
          isBot: true,
          roleColor: '#8a2be2',
          tag: 'BOT',
        },
        timestamp: 'Just now',
        embed: {
          title: '🌌 Side Quest Studio • Support Hub',
          description:
            'Need assistance with server perks, questions, or reporting a rule violation?\n\nClick the button below to start a private ticket with our staff team.',
          color: '#8A2BE2',
          footer: 'Cosmic ki baddie • Support System',
        },
        components: [
          {
            type: 'buttons',
            buttons: [
              {
                id: 'btn-open-ticket-panel',
                label: 'Open Support Ticket',
                style: 'primary',
                emoji: '🎫',
                onClick: () => setTicketModalOpen(true),
              },
            ],
          },
        ],
      };
      setMessages((prev) => [...prev, ticketPanelMsg]);
      return;
    }

    // 5. /giveaway start
    if (lower.startsWith('/giveaway') || lower.startsWith('!giveaway')) {
      const gaMsg: DiscordMessage = {
        id: `bot-${Date.now()}`,
        channelId,
        author: {
          name: 'Cosmic ki baddie',
          avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
          isBot: true,
          roleColor: '#8a2be2',
          tag: 'BOT',
        },
        timestamp: 'Just now',
        embed: {
          title: '🎉 GIVEAWAY: Steam $20 Gift Card',
          description: 'Click below to enter the giveaway!\n\n**Winners:** 1\n**Hosted by:** <@You>\n**Duration:** 1 hour',
          color: '#8A2BE2',
          footer: 'Side Quest Studio Giveaways',
        },
        components: [
          {
            type: 'buttons',
            buttons: [
              {
                id: 'btn-ga-entry',
                label: 'Enter Giveaway 🎉',
                style: 'primary',
                emoji: '🎉',
                onClick: () => handleGiveawayEnter(),
              },
            ],
          },
        ],
      };
      setMessages((prev) => [...prev, gaMsg]);
      return;
    }

    // 6. /poll create
    if (lower.startsWith('/poll') || lower.startsWith('!poll')) {
      const total = (pollVotes[0] || 0) + (pollVotes[1] || 0) + (pollVotes[2] || 0);
      const t0 = calculatePollTally(pollVotes, 0, total, 8);
      const t1 = calculatePollTally(pollVotes, 1, total, 8);
      const t2 = calculatePollTally(pollVotes, 2, total, 8);

      const pollMsg: DiscordMessage = {
        id: `bot-${Date.now()}`,
        channelId,
        author: {
          name: 'Cosmic ki baddie',
          avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
          isBot: true,
          roleColor: '#8a2be2',
          tag: 'BOT',
        },
        timestamp: 'Just now',
        embed: {
          title: '📊 Community Poll: Next Server Game Night?',
          description:
            `1. **Valorant** (${t0.count} votes • ${t0.percentage.toFixed(0)}%)\n\`${t0.progressBar}\`\n\n` +
            `2. **Minecraft Realm** (${t1.count} votes • ${t1.percentage.toFixed(0)}%)\n\`${t1.progressBar}\`\n\n` +
            `3. **Lethal Company** (${t2.count} votes • ${t2.percentage.toFixed(0)}%)\n\`${t2.progressBar}\``,
          color: '#00E5FF',
          footer: 'Cast your vote using the buttons below',
        },
        components: [
          {
            type: 'buttons',
            buttons: [
              { id: 'poll-0', label: '1. Valorant', style: 'secondary', onClick: () => handlePollVote(0) },
              { id: 'poll-1', label: '2. Minecraft', style: 'secondary', onClick: () => handlePollVote(1) },
              { id: 'poll-2', label: '3. Lethal Company', style: 'secondary', onClick: () => handlePollVote(2) },
            ],
          },
        ],
      };
      setMessages((prev) => [...prev, pollMsg]);
      return;
    }

    // 7. /warn or /ban
    if (lower.startsWith('/warn') || lower.startsWith('!warn')) {
      const warnMsg: DiscordMessage = {
        id: `bot-${Date.now()}`,
        channelId,
        author: {
          name: 'Cosmic ki baddie',
          avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
          isBot: true,
          roleColor: '#8a2be2',
          tag: 'BOT',
        },
        timestamp: 'Just now',
        embed: {
          title: '🛡️ Warning Issued (#42)',
          description: `**Target:** <@RuleBreaker> (\`9821471029\`)\n**Total Warnings:** 1\n**Reason:** Disrespect in general chat\n**Moderator:** <@You>`,
          color: '#FFB300',
          footer: 'Logged to #mod-logs and stored in SQLite',
        },
      };
      setMessages((prev) => [...prev, warnMsg]);
      return;
    }

    // 8. /purge
    if (lower.startsWith('/purge') || lower.startsWith('!purge')) {
      const purgeMsg: DiscordMessage = {
        id: `bot-${Date.now()}`,
        channelId,
        author: {
          name: 'Cosmic ki baddie',
          avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
          isBot: true,
          roleColor: '#8a2be2',
          tag: 'BOT',
        },
        timestamp: 'Just now',
        embed: {
          title: '✅ Purge Completed',
          description: `Successfully cleaned **15** messages from <#${channelId}>.\n**Filters Applied:** None (all within 14-day limit)`,
          color: '#00FF88',
          footer: `Requested by You`,
        },
      };
      setMessages((prev) => [...prev, purgeMsg]);
      return;
    }

    // 9. /rank
    if (lower === '/rank' || lower === '!rank') {
      const rankMsg: DiscordMessage = {
        id: `bot-${Date.now()}`,
        channelId,
        author: {
          name: 'Cosmic ki baddie',
          avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
          isBot: true,
          roleColor: '#8a2be2',
          tag: 'BOT',
        },
        timestamp: 'Just now',
        embed: {
          title: '⭐ Activity Profile • You (Traveler)',
          description: `**Level:** 8\n**XP:** \`840 / 900\`\n**Total Messages:** 215\n**Voice Activity:** 3.5 hrs\n**Rank:** #12 of 1,420 members`,
          color: '#8A2BE2',
          footer: 'Side Quest Studio Progression System',
        },
      };
      setMessages((prev) => [...prev, rankMsg]);
      return;
    }

    // Default polite acknowledgement for unmapped text
    if (lower.startsWith('/') || lower.startsWith('!')) {
      sendBotMessage(channelId, `Command \`${text}\` executed successfully. Recorded in SQLite log.`);
    }
  };

  const sendBotMessage = (channelId: string, content: string) => {
    const reply: DiscordMessage = {
      id: `bot-${Date.now()}`,
      channelId,
      author: {
        name: 'Cosmic ki baddie',
        avatar: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=128&auto=format&fit=crop&q=80',
        isBot: true,
        roleColor: '#8a2be2',
        tag: 'BOT',
      },
      timestamp: 'Just now',
      content,
    };
    setMessages((prev) => [...prev, reply]);
  };

  const currentChannelMessages = messages.filter((m) => m.channelId === activeChannelId);
  const activeChannelObj = channels.find((c) => c.id === activeChannelId);

  return (
    <div className="flex flex-col h-[calc(100vh-13rem)] min-h-[580px] bg-[#313338] text-gray-200 rounded-xl overflow-hidden border border-purple-900/40 shadow-2xl">
      {/* Discord Top Server Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#2b2d31] border-b border-[#1f2023] text-sm">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-600 to-cyan-500 flex items-center justify-center font-bold text-white shadow">
            SQ
          </div>
          <div>
            <div className="font-semibold text-white flex items-center gap-1.5">
              Side Quest Studio
              <span className="text-[10px] bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded font-mono">
                Cosmic Engine
              </span>
            </div>
            <div className="text-[11px] text-gray-400">1,420 Travelers • Managed by Cosmic ki baddie</div>
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-400">
          <span className="flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded border border-emerald-500/30">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Bot Online (WAL SQLite)
          </span>
          <span className="bg-[#1e1f22] px-2 py-1 rounded text-purple-300 font-mono">
            Prefix: !
          </span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Discord Channel Sidebar */}
        <div className="w-56 bg-[#2b2d31] flex flex-col justify-between border-r border-[#1f2023] select-none">
          <div className="overflow-y-auto p-2 space-y-1">
            <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider px-2 py-1">
              Text Channels
            </div>
            {channels.map((ch) => {
              const isActive = ch.id === activeChannelId;
              const isTicket = ch.type === 'ticket';
              return (
                <button
                  key={ch.id}
                  onClick={() => setActiveChannelId(ch.id)}
                  className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded text-sm transition-all text-left ${
                    isActive
                      ? 'bg-[#35373c] text-white font-medium'
                      : 'text-gray-400 hover:bg-[#35373c]/50 hover:text-gray-200'
                  }`}
                >
                  {isTicket ? (
                    <Ticket className="w-4 h-4 text-purple-400 shrink-0" />
                  ) : (
                    <Hash className="w-4 h-4 text-gray-500 shrink-0" />
                  )}
                  <span className="truncate">{ch.name}</span>
                </button>
              );
            })}
          </div>

          {/* User profile footer */}
          <div className="p-2.5 bg-[#232428] flex items-center justify-between border-t border-[#1f2023]">
            <div className="flex items-center gap-2">
              <div className="relative">
                <img
                  src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=64&auto=format&fit=crop&q=80"
                  alt="You"
                  className="w-8 h-8 rounded-full object-cover"
                />
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 border-2 border-[#232428] rounded-full" />
              </div>
              <div className="text-xs">
                <div className="font-semibold text-white">You</div>
                <div className="text-gray-400 text-[10px]">Traveler #0001</div>
              </div>
            </div>
            <Shield className="w-4 h-4 text-purple-400" title="Side Quest Member" />
          </div>
        </div>

        {/* Center Chat Area */}
        <div className="flex-1 flex flex-col bg-[#313338] overflow-hidden">
          {/* Channel Header */}
          <div className="h-12 px-4 flex items-center justify-between bg-[#313338] border-b border-[#202225] shrink-0">
            <div className="flex items-center gap-2">
              <Hash className="w-5 h-5 text-gray-400" />
              <span className="font-bold text-white text-sm">{activeChannelObj?.name}</span>
              <span className="text-gray-400 text-xs hidden md:inline-block border-l border-gray-600 pl-2">
                {activeChannelObj?.topic}
              </span>
            </div>
            <div className="flex items-center gap-3 text-gray-400 text-sm">
              <Bell className="w-4 h-4 hover:text-white cursor-pointer" />
              <Pin className="w-4 h-4 hover:text-white cursor-pointer" />
              <Users className="w-4 h-4 hover:text-white cursor-pointer" />
            </div>
          </div>

          {/* Message Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {currentChannelMessages.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <Hash className="w-12 h-12 mx-auto mb-2 text-gray-500" />
                <h3 className="text-lg font-bold text-white">Welcome to #{activeChannelObj?.name}!</h3>
                <p className="text-xs mt-1">This is the start of the #{activeChannelObj?.name} channel.</p>
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  <button
                    onClick={() => setInputText('!help')}
                    className="text-xs bg-[#2b2d31] hover:bg-[#35373c] px-3 py-1.5 rounded border border-purple-500/30 text-purple-300"
                  >
                    Send !help
                  </button>
                  <button
                    onClick={() => setInputText('/dashboard')}
                    className="text-xs bg-[#2b2d31] hover:bg-[#35373c] px-3 py-1.5 rounded border border-purple-500/30 text-purple-300"
                  >
                    Send /dashboard
                  </button>
                </div>
              </div>
            ) : (
              currentChannelMessages.map((m) => (
                <div key={m.id} className="flex items-start gap-3 group hover:bg-[#2e3035] -mx-4 px-4 py-1.5 rounded">
                  <img
                    src={m.author.avatar}
                    alt={m.author.name}
                    className="w-10 h-10 rounded-full mt-0.5 object-cover shrink-0"
                  />
                  <div className="flex-1 overflow-hidden">
                    <div className="flex items-baseline gap-2">
                      <span
                        className="font-semibold text-sm hover:underline cursor-pointer"
                        style={{ color: m.author.roleColor || '#ffffff' }}
                      >
                        {m.author.name}
                      </span>
                      {m.author.isBot && (
                        <span className="bg-[#5865f2] text-white text-[10px] font-bold px-1.5 py-0.2 rounded font-sans uppercase">
                          BOT
                        </span>
                      )}
                      <span className="text-[11px] text-gray-400">{m.timestamp}</span>
                    </div>

                    {m.content && (
                      <div className="text-sm mt-0.5 text-gray-200 break-words">{formatDiscordText(m.content)}</div>
                    )}

                    {/* Discord Embed */}
                    {m.embed && (
                      <div
                        className="mt-2 rounded border-l-4 bg-[#2b2d31] p-3 text-sm max-w-xl shadow"
                        style={{ borderLeftColor: m.embed.color || '#8A2BE2' }}
                      >
                        {m.embed.title && (
                          <div className="font-bold text-white text-base mb-1">{m.embed.title}</div>
                        )}
                        {m.embed.description && (
                          <div className="text-gray-300 text-xs leading-relaxed">
                            {formatDiscordText(m.embed.description)}
                          </div>
                        )}
                        {m.embed.fields && (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2 pt-2 border-t border-gray-700/50">
                            {m.embed.fields.map((f, idx) => (
                              <div key={idx} className="text-xs">
                                <div className="font-semibold text-gray-300">{f.name}</div>
                                <div className="text-gray-400">{f.value}</div>
                              </div>
                            ))}
                          </div>
                        )}
                        {m.embed.footer && (
                          <div className="text-[10px] text-gray-400 mt-2 pt-1 border-t border-gray-700/40">
                            {m.embed.footer}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Discord Component Buttons */}
                    {m.components?.map((c, cIdx) => (
                      <div key={cIdx} className="mt-2.5 flex flex-wrap gap-2">
                        {c.buttons?.map((btn) => {
                          const styleClasses = {
                            primary: 'bg-[#5865f2] hover:bg-[#4752c4] text-white',
                            secondary: 'bg-[#4e5058] hover:bg-[#6d6f78] text-white',
                            success: 'bg-[#248046] hover:bg-[#1a6334] text-white',
                            danger: 'bg-[#da373c] hover:bg-[#a1282c] text-white',
                          }[btn.style];

                          return (
                            <button
                              key={btn.id}
                              onClick={btn.onClick}
                              disabled={btn.disabled}
                              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition active:scale-95 shadow ${styleClasses}`}
                            >
                              {btn.emoji && <span>{btn.emoji}</span>}
                              <span>{btn.label}</span>
                            </button>
                          );
                        })}
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Action Chips */}
          <div className="px-4 py-1.5 bg-[#2b2d31] border-t border-[#202225] flex items-center gap-2 overflow-x-auto text-xs shrink-0">
            <span className="text-[11px] text-gray-400 uppercase font-semibold shrink-0">Quick Run:</span>
            {[
              { label: '!help', cmd: '!help' },
              { label: '/dashboard', cmd: '/dashboard' },
              { label: '/ticket panel', cmd: '/ticket panel' },
              { label: '/giveaway start', cmd: '/giveaway start' },
              { label: '/poll create', cmd: '/poll create' },
              { label: 'hello', cmd: 'hello' },
              { label: 'rules', cmd: 'rules' },
              { label: '!rank', cmd: '!rank' },
              { label: '/purge 10', cmd: '/purge 10' },
            ].map((chip) => (
              <button
                key={chip.label}
                onClick={() => setInputText(chip.cmd)}
                className="bg-[#1e1f22] hover:bg-[#35373c] text-purple-300 hover:text-white px-2.5 py-1 rounded transition text-xs font-mono shrink-0 border border-purple-900/30"
              >
                {chip.label}
              </button>
            ))}
          </div>

          {/* Chat Input Bar */}
          <div className="p-4 bg-[#313338] shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center bg-[#383a40] rounded-lg px-4 py-2.5"
            >
              <PlusCircle className="w-5 h-5 text-gray-400 mr-3 hover:text-white cursor-pointer" />
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder={`Message #${activeChannelObj?.name} (Try !help or /dashboard)...`}
                className="flex-1 bg-transparent text-sm text-white focus:outline-none placeholder-gray-500"
              />
              <button
                type="submit"
                disabled={!inputText.trim()}
                className="text-purple-400 hover:text-purple-300 disabled:opacity-40 transition ml-2"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Interactive Modal for Ticket Creation */}
      {ticketModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="bg-[#313338] border border-purple-500/40 rounded-lg max-w-md w-full shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-[#202225] flex justify-between items-center bg-[#2b2d31]">
              <h3 className="font-bold text-white flex items-center gap-2">
                <Ticket className="w-4 h-4 text-purple-400" />
                Open a Support Ticket
              </h3>
              <button
                onClick={() => setTicketModalOpen(false)}
                className="text-gray-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-xs uppercase font-bold text-gray-300 mb-1">
                  Ticket Subject / Issue <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={ticketSubject}
                  onChange={(e) => setTicketSubject(e.target.value)}
                  placeholder="e.g. VIP Role Inquiries or Rule Violation"
                  className="w-full bg-[#1e1f22] border border-gray-700 rounded p-2.5 text-sm text-white focus:border-purple-500 focus:outline-none"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-xs uppercase font-bold text-gray-300 mb-1">
                  Detailed Explanation
                </label>
                <textarea
                  rows={3}
                  value={ticketDetails}
                  onChange={(e) => setTicketDetails(e.target.value)}
                  placeholder="Provide context for the Side Quest Studio staff team..."
                  className="w-full bg-[#1e1f22] border border-gray-700 rounded p-2.5 text-sm text-white focus:border-purple-500 focus:outline-none"
                />
              </div>
            </div>
            <div className="p-4 bg-[#2b2d31] flex justify-end gap-2 border-t border-[#202225]">
              <button
                type="button"
                onClick={() => setTicketModalOpen(false)}
                className="px-4 py-2 text-sm text-gray-300 hover:underline"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={createTicketChannel}
                disabled={!ticketSubject.trim()}
                className="px-5 py-2 bg-[#5865f2] hover:bg-[#4752c4] disabled:opacity-50 text-white rounded font-medium text-sm transition shadow"
              >
                Submit Ticket
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
